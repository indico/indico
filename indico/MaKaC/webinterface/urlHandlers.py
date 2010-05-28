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

from MaKaC.common.url import URL
from MaKaC.common.Configuration import Config
import string
import MaKaC.user as user
from new import classobj
from MaKaC.common.utils import utf8rep

"""
This file contains classes representing url handlers which are objects which
contain information about every request handler of the application and which are
responsible for generating the correct url for a given request handler given
certain parameters. This file is a kind URL database so other web interface
modules will use the classes instead of using harcoded urls; this makes possible
to eassily change the urls or the parameter names without affecting the rest of
the system.
"""

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
    """
    _relativeURL = "broken link"

    @classmethod
    def getRelativeURL( cls ):
        """Gives the relative URL (URL part which is carachteristic) for the
            corresponding request handler.
        """
        return cls._relativeURL

    @classmethod
    def _getURL( cls, **params ):
        """ Gives the full URL for the corresponding request handler.

            Parameters:
                params - (Dict) parameters to be added to the URL.
        """
        return URL( "%s/%s"%(Config.getInstance().getBaseURL(),cls.getRelativeURL()) , **params )

    @classmethod
    def getURL( cls, target=None, **params ):
        """Gives the full URL for the corresponding request handler. In case
            the target parameter is specified it will append to the URL the
            the necessary parameters to make the target be specified in the url.

            Parameters:
                target - (Locable) Target object which must be uniquely
                    specified in the URL so the destination request handler
                    is able to retrieve it.
                params - (Dict) parameters to be added to the URL.
        """
        url = cls._getURL(**params)
        if target is not None:
            url.addParams( target.getLocator() )
        return url

class SecureURLHandler(URLHandler):

    @classmethod
    def _getURL(cls, **params):
        return URL( "%s/%s"%(Config.getInstance().getBaseSecureURL(), cls.getRelativeURL()) , **params )

class OptionallySecureURLHandler(URLHandler):

    @classmethod
    def getURL( cls, target=None, secure = False, **params ):
        if secure:
            url = URL( "%s/%s"%(Config.getInstance().getBaseSecureURL(), cls.getRelativeURL()) , **params )
        else:
            url = URL( "%s/%s"%(Config.getInstance().getBaseURL(),cls.getRelativeURL()) , **params )
        if target is not None:
            url.addParams( target.getLocator() )
        return url

__URLHandlerClassCounter = 0;

def Build(relativeURL):
    global __URLHandlerClassCounter
    __URLHandlerClassCounter += 1
    return classobj("__UHGenerated" + str(__URLHandlerClassCounter), (URLHandler,), {"_relativeURL": relativeURL})

def Derive(handler, relativeURL):
    if not issubclass(handler, URLHandler):
        handler = handler._uh;
    return Build(handler._relativeURL + "/" + relativeURL)

# Hack to allow secure Indico on non-80 ports
def setSSLPort( url ):
    """
    Returns url with port changed to SSL one.
    If url has no port specified, it returns the same url.
    SSL port is extracted from loginURL (MaKaCConfig)
    """
    # Set proper PORT for images requested via SSL
    loginURL = Config.getInstance().getLoginURL()
    try:
        colonIx = loginURL.index( ':', 6 )     # Colon after https:// means port
        slashIx = loginURL.index( '/', colonIx )
        if slashIx <= colonIx:
            slashIx = len( loginURL )
        sslPort = loginURL[colonIx+1:slashIx]  # like "8443"
    except ValueError:
        sslPort = "443"

    sslPort = ':' + sslPort     # like ":8443/"

    # If there is NO port, nothing will happen (production indico)
    # If there IS port, it will be replaced with proper SSL one, taken from loginURL
    import re
    regexp = ':\d{2,5}'   # Examples:   :8080   :80   :65535
    return re.sub( regexp, sslPort, url )


class UHWelcome( URLHandler ):
    _relativeURL = "index.py"


class UHSignIn( URLHandler ):
    _relativeURL = "signIn.py"

    def getURL( cls, returnURL="" ):
        if Config.getInstance().getLoginURL() != "":
            url = URL(Config.getInstance().getLoginURL())
        else:
            url = cls._getURL()
        if str(returnURL).strip() != "":
            url.addParam( "returnURL", returnURL )
        return url
    getURL = classmethod( getURL )


class UHActiveAccount( URLHandler ):
    _relativeURL = "signIn.py/active"


class UHSendActivation( URLHandler ):
    _relativeURL = "signIn.py/sendActivation"


class UHDisabledAccount( URLHandler ):
    _relativeURL = "signIn.py/disabledAccount"


class UHSendLogin( URLHandler ):
    _relativeURL = "signIn.py/sendLogin"


class UHUnactivatedAccount( URLHandler ):
    _relativeURL = "signIn.py/unactivatedAccount"

class UHSignOut( URLHandler ):
    _relativeURL = "logOut.py"

    def getURL( cls, returnURL="" ):
        url = cls._getURL()
        if str(returnURL).strip() != "":
            url.addParam( "returnURL", returnURL )
        return url
    getURL = classmethod( getURL )

class UHIndicoNews( URLHandler ):
    _relativeURL = "news.py"

class UHConferenceHelp(URLHandler):
    _relativeURL ="help.py"

class UHSearch(URLHandler):
    _relativeURL ="search.py"

class UHCalendar( URLHandler ):
    _relativeURL = "wcalendar.py"

    def getURL( cls, categList = None ):
        url = cls._getURL()
        if not categList:
            categList = []
        l = []
        for categ in categList:
            l.append( categ.getId() )
        url.addParam( "selCateg", l )
        return url
    getURL = classmethod( getURL )


class UHCalendarSelectCategories( URLHandler ):
    _relativeURL = "wcalendar.py/select"


class UHSimpleCalendar( URLHandler ):
    _relativeURL = "calendarSelect.py"

class UHSimpleColorChart( URLHandler ):
    _relativeURL = "colorSelect.py"

class UHConferenceCreation( URLHandler ):
    _relativeURL = "conferenceCreation.py"
    @classmethod
    def getURL( cls, target):
        url = cls._getURL()
        if target is not None:
            url.addParams( target.getLocator() )
        return url

class UHConferencePerformCreation( URLHandler ):
    _relativeURL = "conferenceCreation.py/createConference"

class UHConferenceDisplay( URLHandler ):
    _relativeURL = "conferenceDisplay.py"

class UHConferenceOverview( URLHandler ):
    _relativeURL = "conferenceDisplay.py"

    @classmethod
    def getURL( cls, target ):
        url = cls._getURL()
        if target is not None:
            url.addParams( target.getLocator() )
        url.addParam( 'ovw', True )
        return url

class UHConferenceEmail(URLHandler):
    _relativeURL = "EMail.py"

class UHConferenceSendEmail(URLHandler):
    _relativeURL = "EMail.py/send"

class UHRegistrantsSendEmail(URLHandler):
    _relativeURL = "EMail.py/sendreg"

class UHConvenersSendEmail(URLHandler):
    _relativeURL = "EMail.py/sendconvener"

class UHAuthorSendEmail(URLHandler):
    _relativeURL = "EMail.py/authsend"

class UHContribParticipantsSendEmail(URLHandler):
    _relativeURL = "EMail.py/sendcontribparticipants"

class UHConferenceOtherViews( URLHandler ):
    _relativeURL = "conferenceOtherViews.py"


class UHConferenceLogo( URLHandler ):
    _relativeURL = "conferenceDisplay.py/getLogo"


class UHConferenceCSS( URLHandler ):
    _relativeURL = "conferenceDisplay.py/getCSS"

class UHConferencePic( URLHandler ):
    _relativeURL = "conferenceDisplay.py/getPic"

class UHConfModifPreviewCSS(URLHandler):
    _relativeURL = "confModifDisplay.py/previewCSS"

class UHCategoryIcon( URLHandler ):
    _relativeURL = "categoryDisplay.py/getIcon"

class UHConferenceModification( URLHandler ):
    _relativeURL = "conferenceModification.py"

class UHConfModifShowMaterials( URLHandler ):
    _relativeURL = "conferenceModification.py/materialsShow"

class UHConfModifAddMaterials( URLHandler ):
    _relativeURL = "conferenceModification.py/materialsAdd"

# ============================================================================
# ROOM BOOKING ===============================================================
# ============================================================================

# Free standing ==============================================================

class UHRoomBookingMapOfRooms( URLHandler ):

    def getURL( cls, returnURL="" ):
        return "http://gs-dep.web.cern.ch/gs-dep/groups/SEM/ce/isp/conf_rooms/conf_rooms.html"
    getURL = classmethod( getURL )



class UHRoomBookingWelcome( URLHandler ):
    _relativeURL = "roomBooking.py"

class UHRoomBookingSearch4Rooms( URLHandler ):
    _relativeURL = "roomBooking.py/search4Rooms"
    @classmethod
    def getURL( cls, forNewBooking = False ):
        url = cls._getURL()
        if forNewBooking:
            url.addParam( 'forNewBooking', True )
        else:
            url.addParam( 'forNewBooking', False )
        return url

class UHRoomBookingSearch4Bookings( URLHandler ):
    _relativeURL = "roomBooking.py/search4Bookings"
class UHRoomBookingSearch4Users( URLHandler ):
    _relativeURL = "roomBooking.py/search4Users"

class UHRoomBookingRoomList( URLHandler ):
    _relativeURL = "roomBooking.py/roomList"
    @classmethod
    def getURL( cls, onlyMy = False ):
        url = cls._getURL()
        if onlyMy:
            url.addParam( 'onlyMy', 'on' )
        return url
class UHRoomBookingBookingList( URLHandler ):
    _relativeURL = "roomBooking.py/bookingList"
    @classmethod
    def getURL( cls, onlyMy = False, ofMyRooms = False, onlyPrebookings = False, autoCriteria = False, newParams = None, today = False, allRooms = False ):
        """
        onlyMy - only bookings of the current user
        ofMyRooms - only bookings for rooms managed by the current user
        autoCriteria - some reasonable constraints, like "only one month ahead"
        """
        url = cls._getURL()
        if onlyMy:
            url.addParam( 'onlyMy', 'on' )
        if ofMyRooms:
            url.addParam( 'ofMyRooms', 'on' )
        if onlyPrebookings:
            url.addParam( 'onlyPrebookings', 'on' )
        if autoCriteria:
            url.addParam( 'autoCriteria', 'True' )
        if today:
            url.addParam( 'day', 'today' )
        if allRooms:
            url.addParam( 'roomGUID', 'allRooms' )
        if newParams:
            url.setParams( newParams )
        return url

class UHRoomBookingRoomDetails( URLHandler ):
    _relativeURL = "roomBooking.py/roomDetails"

    @classmethod
    def getURL( cls, target = None, calendarMonths = None ):
        """
        onlyMy - only bookings of the current user
        ofMyRooms - only bookings for rooms managed by the current user
        autoCriteria - some reasonable constraints, like "only one month ahead"
        """
        url = cls._getURL()
        if target:
            url.setParams( target.getLocator() )
        if calendarMonths:
            url.addParam( 'calendarMonths', 'True' )
        return url

class UHRoomBookingRoomStats( URLHandler ):
    _relativeURL = "roomBooking.py/roomStats"

class UHRoomBookingBookingDetails( URLHandler ):
    _relativeURL = "roomBooking.py/bookingDetails"

class UHRoomBookingRoomForm( URLHandler ):
    _relativeURL = "roomBooking.py/roomForm"
class UHRoomBookingSaveRoom( URLHandler ):
    _relativeURL = "roomBooking.py/saveRoom"
class UHRoomBookingDeleteRoom( URLHandler ):
    _relativeURL = "roomBooking.py/deleteRoom"

class UHRoomBookingBookingForm( URLHandler ):
    _relativeURL = "roomBooking.py/bookingForm"
class UHRoomBookingSaveBooking( URLHandler ):
    _relativeURL = "roomBooking.py/saveBooking"
class UHRoomBookingDeleteBooking( URLHandler ):
    _relativeURL = "roomBooking.py/deleteBooking"
class UHRoomBookingCloneBooking( URLHandler ):
    _relativeURL = "roomBooking.py/cloneBooking"
class UHRoomBookingCancelBooking( URLHandler ):
    _relativeURL = "roomBooking.py/cancelBooking"
class UHRoomBookingAcceptBooking( URLHandler ):
    _relativeURL = "roomBooking.py/acceptBooking"
class UHRoomBookingRejectBooking( URLHandler ):
    _relativeURL = "roomBooking.py/rejectBooking"
class UHRoomBookingRejectAllConflicting( URLHandler):
    _relativeURL = "roomBooking.py/rejectAllConflicting"
class UHRoomBookingRejectBookingOccurrence( URLHandler ):
    _relativeURL = "roomBooking.py/rejectBookingOccurrence"

    @classmethod
    def getURL( cls, target, date ):
        url = cls._getURL()
        if target:
            url.setParams( target.getLocator() )
        if date:
            url.addParam( 'date', date )
        return url

class UHRoomBookingCancelBookingOccurrence( URLHandler ):
    _relativeURL = "roomBooking.py/cancelBookingOccurrence"

    @classmethod
    def getURL( cls, target, date ):
        url = cls._getURL()
        if target:
            url.setParams( target.getLocator() )
        if date:
            url.addParam( 'date', date )
        return url


class UHRoomBookingStatement( URLHandler ):
    _relativeURL = "roomBooking.py/statement"

# RB Administration

class UHRoomBookingPluginAdmin( URLHandler ):
    _relativeURL = "roomBookingPluginAdmin.py"

class UHRoomBookingModuleActive( URLHandler ):
    _relativeURL = "roomBookingPluginAdmin.py/switchRoomBookingModuleActive"

class UHRoomBookingPlugAdminZODBSave( URLHandler ):
    _relativeURL = "roomBookingPluginAdmin.py/zodbSave"

class UHRoomBookingAdmin( URLHandler ):
    _relativeURL = "roomBooking.py/admin"

class UHRoomBookingAdminLocation( URLHandler ):
    _relativeURL = "roomBooking.py/adminLocation"

class UHRoomBookingSetDefaultLocation( URLHandler ):
    _relativeURL = "roomBooking.py/setDefaultLocation"
class UHRoomBookingSaveLocation( URLHandler ):
    _relativeURL = "roomBooking.py/saveLocation"
class UHRoomBookingDeleteLocation( URLHandler ):
    _relativeURL = "roomBooking.py/deleteLocation"
class UHRoomBookingSaveEquipment( URLHandler ):
    _relativeURL = "roomBooking.py/saveEquipment"
class UHRoomBookingDeleteEquipment( URLHandler ):
    _relativeURL = "roomBooking.py/deleteEquipment"

class UHRoomBookingSaveCustomAttributes( URLHandler ):
    _relativeURL = "roomBooking.py/saveCustomAttributes"
class UHRoomBookingDeleteCustomAttribute( URLHandler ):
    _relativeURL = "roomBooking.py/deleteCustomAttribute"

class UHRoomBookingGetDateWarning( URLHandler ):
    _relativeURL = "roomBooking.py/getDateWarning"

class UHRoomBookingGetRoomSelectList( URLHandler ):
    _relativeURL = "roomBooking.py/getRoomSelectList"

class UHRoomBookingGetRoomSelectList4SubEvents( URLHandler ):
    _relativeURL = "roomBooking.py/getRoomSelectList4SubEvents"


# For the event ==============================================================


class UHConfModifRoomBookingChooseEvent( URLHandler ):
    _relativeURL = "conferenceModification.py/roomBookingChooseEvent"

class UHConfModifRoomBookingSearch4Rooms( URLHandler ):
    _relativeURL = "conferenceModification.py/roomBookingSearch4Rooms"

    @classmethod
    def getURL( cls, target = None, dontAssign = False  ):
        url = cls._getURL()
        if target:
            url.setParams( target.getLocator() )
        if dontAssign:
            url.addParam( "dontAssign", True )
        return url

class UHConfModifRoomBookingList( URLHandler ):
    _relativeURL = "conferenceModification.py/roomBookingList"
class UHConfModifRoomBookingRoomList( URLHandler ):
    _relativeURL = "conferenceModification.py/roomBookingRoomList"

class UHConfModifRoomBookingDetails( URLHandler ):
    _relativeURL = "conferenceModification.py/roomBookingDetails"
class UHConfModifRoomBookingRoomDetails( URLHandler ):
    _relativeURL = "conferenceModification.py/roomBookingRoomDetails"

class UHConfModifRoomBookingBookingForm( URLHandler ):
    _relativeURL = "conferenceModification.py/roomBookingBookingForm"
class UHConfModifRoomBookingSaveBooking( URLHandler ):
    _relativeURL = "conferenceModification.py/roomBookingSaveBooking"


class UHRoomPhoto( URLHandler ):
    _relativeTemplate = "images/rooms/large_photos/%s.jpg"

    @classmethod
    def getURL( cls, target = None ):
        cls._relativeURL = cls._relativeTemplate % str( target )
        return cls._getURL()

class UHRoomPhotoSmall( URLHandler ):
    _relativeTemplate = "images/rooms/small_photos/%s.jpg"

    @classmethod
    def getURL( cls, target = None ):
        cls._relativeURL = cls._relativeTemplate % str( target )
        return cls._getURL()

# Used (?) to send room photos via Python script
#class UHSendRoomPhoto( URLHandler ):
#    _relativeURL = "roomBooking.py/sendRoomPhoto"
#
#    @classmethod
#    def getURL( cls, photoId, small ):
#        url = cls._getURL()
#        url.addParam( "photoId", photoId )
#        url.addParam( "small", small )
#        return url


class UHConfModChairNew( URLHandler ):
    _relativeURL = "conferenceModification.py/newChair"


class UHConferenceRemoveChairs( URLHandler ):
    _relativeURL = "conferenceModification.py/removeChairs"


class UHConfModChairEdit( URLHandler ):
    _relativeURL = "conferenceModification.py/editChair"

class UHConfModifSelectChairs( URLHandler ):
    _relativeURL = "conferenceModification.py/selectChairs"


class UHConfModifAddChairs( URLHandler ):
    _relativeURL = "conferenceModification.py/addChairs"

class UHConferenceAddMaterial( URLHandler ):
    _relativeURL = "conferenceModification.py/addMaterial"


class UHConferencePerformAddMaterial( URLHandler ):
    _relativeURL = "conferenceModification.py/performAddMaterial"


class UHConferenceRemoveMaterials( URLHandler ):
    _relativeURL = "conferenceModification.py/removeMaterials"


class UHConfModSessionSlots( URLHandler ):
    _relativeURL = "conferenceModification.py/sessionSlots"

class UHConferenceClose( URLHandler ):
    _relativeURL = "conferenceModification.py/close"

class UHConferenceDeleteSocialEvent( URLHandler ):
    _relativeURL = "conferenceModification.py/deleteSocialEvent"

class UHConferenceModificationClosed( URLHandler ):
    _relativeURL = "conferenceModification.py/modificationClosed"

class UHConferenceOpen( URLHandler ):
    _relativeURL = "conferenceModification.py/open"

class UHConfDataModif( URLHandler ):
    _relativeURL = "conferenceModification.py/data"
    @classmethod
    def getURL( cls, target):
        url = cls._getURL()
        if target is not None:
            url.addParams( target.getLocator() )
        return url

class UHConfScreenDatesEdit( URLHandler ):
    _relativeURL = "conferenceModification.py/screenDates"

class UHConfPerformDataModif( URLHandler ):
    _relativeURL = "conferenceModification.py/dataPerform"


class UHConfAddContribType( URLHandler ):
    _relativeURL = "conferenceModification.py/addContribType"


class UHConfRemoveContribType( URLHandler ):
    _relativeURL = "conferenceModification.py/removeContribType"


class UHConfEditContribType( URLHandler ):
    _relativeURL = "conferenceModification.py/editContribType"

class UHConfSectionsSettings( URLHandler ):
    _relativeURL = "conferenceModification.py/sectionsSettings"

class UHConfModifCFAOptFld( URLHandler ):
    _relativeURL = "confModifCFA.py/abstractFields"

class UHConfModifCFAAddOptFld( URLHandler ):
    _relativeURL = "confModifCFA.py/addAbstractField"

class UHConfModifCFAPerformAddOptFld( URLHandler ):
    _relativeURL = "confModifCFA.py/performAddAbstractField"

class UHConfModifCFAEditOptFld( URLHandler ):
    _relativeURL = "confModifCFA.py/editAbstractField"

class UHConfModifCFARemoveOptFld( URLHandler ):
    _relativeURL = "confModifCFA.py/removeAbstractField"

class UHConfModifCFAAbsFieldUp(URLHandler):
    _relativeURL = "confModifCFA.py/absFieldUp"

class UHConfModifCFAAbsFieldDown(URLHandler):
    _relativeURL = "confModifCFA.py/absFieldDown"

class UHConfModifReportNumberEdit( URLHandler ):
    _relativeURL = "conferenceModification.py/editReportNumber"

class UHConfModifReportNumberPerformEdit( URLHandler ):
    _relativeURL = "conferenceModification.py/performEditReportNumber"

class UHConfModifReportNumberRemove( URLHandler ):
    _relativeURL = "conferenceModification.py/removeReportNumber"

class UHConfModifProgram( URLHandler ):
    _relativeURL = "confModifProgram.py"

class UHConfModifProgramDescription( URLHandler ):
    _relativeURL = "confModifProgram.py/modifyDescription"

class UHConfModifCFA( URLHandler ):
    _relativeURL = "confModifCFA.py"

class UHConfModifCFAPreview( URLHandler ):
    _relativeURL = "confModifCFA.py/preview"

class UHConfCFAChangeStatus( URLHandler ):
    _relativeURL = "confModifCFA.py/changeStatus"

class UHConfCFASwitchMultipleTracks( URLHandler ):
    _relativeURL = "confModifCFA.py/switchMultipleTracks"

class UHConfCFAMakeTracksMandatory( URLHandler ):
    _relativeURL = "confModifCFA.py/makeTracksMandatory"

class UHCFAManagementAddType( URLHandler ):
    _relativeURL = "confModifCFA.py/addType"


class UHCFAManagementRemoveType( URLHandler ):
    _relativeURL = "confModifCFA.py/removeType"


class UHCFADataModification( URLHandler ):
    _relativeURL = "confModifCFA.py/modifyData"


class UHCFAPerformDataModification( URLHandler ):
    _relativeURL = "confModifCFA.py/performModifyData"


class UHCFAModifTemplate( URLHandler ):
    _relativeURL = "CFAModification.py/template"


class UHCFAModifReferee( URLHandler ):
    _relativeURL = "CFAModification.py/referee"


class UHCFASelectReferee( URLHandler ):
    _relativeURL = "CFAModification.py/selectReferee"


class UHCFAAddReferees( URLHandler ):
    _relativeURL = "CFAModification.py/addReferees"


class UHCFARemoveReferee( URLHandler ):
    _relativeURL = "CFAModification.py/deleteReferees"


class UHConfAbstractManagment( URLHandler ):
    _relativeURL = "abstractsManagment.py"


class UHConfAbstractManagmentCloseMenu( URLHandler ):
    _relativeURL = "abstractsManagment.py/closeMenu"


class UHConfAbstractManagmentOpenMenu( URLHandler ):
    _relativeURL = "abstractsManagment.py/openMenu"


class UHAbstractSubmission( URLHandler ):
    _relativeURL = "abstractSubmission.py"

    def getURL( cls, target=None ):
        url = cls._getURL()
        if target:
            url.setParams( target.getLocator() )
        url.setSegment("interest")
        return url
    getURL = classmethod( getURL )


class UHAbstractSubmissionConfirmation( URLHandler ):
    _relativeURL = "abstractSubmission.py/confirmation"


class UHAbstractDisplay( URLHandler ):
    _relativeURL = "abstractDisplay.py"

class UHAbstractDisplayMaterial( URLHandler ):
    _relativeURL = "abstractDisplay.py/material"

class UHAbstractDisplayAddMaterial( URLHandler ):
    _relativeURL = "abstractDisplay.py/addMaterial"

class UHAbstractDisplayPerformAddMaterial( URLHandler ):
    _relativeURL = "abstractDisplay.py/performAddMaterial"

class UHAbstractDisplayRemoveMaterials( URLHandler ):
    _relativeURL = "abstractDisplay.py/removeMaterials"

class UHMaterialDisplayRemoveResource( URLHandler ):
    _relativeURL = "materialDisplay.py/removeResource"

class UHMaterialDisplaySubmitResource( URLHandler ):
    _relativeURL = "materialDisplay.py/submitResource"

class UHAbstractDisplayPDF( URLHandler ):
    _relativeURL = "abstractDisplay.py/pdf"

class UHAbstractsDisplayPDF( URLHandler ):
    _relativeURL = "abstractDisplay.py/abstractsPdf"


class UHAbstractConfManagerDisplayPDF( URLHandler ):
    _relativeURL = "abstractManagment.py/abstractToPDF"


class UHAbstractsConfManagerDisplayPDF( URLHandler ):
    _relativeURL = "abstractsManagment.py/abstractsToPDF"


class UHAbstractConfSelectionAction( URLHandler ):
    _relativeURL = "abstractsManagment.py/abstractsActions"


class UHAbstractsConfManagerDisplayParticipantList( URLHandler ):
    _relativeURL = "abstractsManagment.py/participantList"


class UHAbstractsConfManagerDisplayXML( URLHandler ):
    _relativeURL = "abstractsManagment.py/abstractsToXML"


class UHAbstractsConfManagerDisplayExcel( URLHandler ):
    _relativeURL = "abstractsManagment.py/abstractsListToExcel"


class UHAbstractsTrackManagerParticipantList( URLHandler ):
    _relativeURL = "trackModifAbstracts.py/participantList"


class UHAbstractsTrackManagerDisplayPDF( URLHandler ):
    _relativeURL = "trackModifAbstracts.py/abstractsToPDF"


class UHAbstractstrackManagerDisplayPDF( URLHandler ):
    _relativeURL = "trackModifAbstracts.py/abstractsToPDF"


class UHUserAbstracts( URLHandler ):
    _relativeURL = "userAbstracts.py"


class UHAbstractModify( URLHandler ):
    _relativeURL = "abstractModify.py"

    def getURL( cls, target=None ):
        url = cls._getURL()
        if target:
            url.setParams( target.getLocator() )
        url.setSegment("interest")
        return url
    getURL = classmethod( getURL )


class UHCFAModifAbstracts( URLHandler ):
    _relativeURL = "CFAModification.py/abstracts"


class UHCFAAbstractManagment( URLHandler ):
    _relativeURL = "abstractManagment.py"


class UHAbstractManagment( URLHandler ):
    _relativeURL = "abstractManagment.py"


class UHAbstractManagmentAccept( URLHandler ):
    _relativeURL = "abstractManagment.py/accept"


class UHAbstractManagmentAcceptMultiple( URLHandler ):
    _relativeURL = "abstractManagment.py/acceptMultiple"


class UHAbstractManagmentRejectMultiple( URLHandler ):
    _relativeURL = "abstractManagment.py/rejectMultiple"


class UHAbstractManagmentReject( URLHandler ):
    _relativeURL = "abstractManagment.py/reject"


class UHAbstractManagmentChangeTrack( URLHandler ):
    _relativeURL = "abstractManagment.py/changeTrack"


class UHAbstractTrackProposalManagment( URLHandler ):
    _relativeURL = "abstractManagment.py/trackProposal"


class UHCFAAbstractDeletion( URLHandler ):
    _relativeURL = "abstractManagment.py/deleteAbstract"


class UHAbstractDirectAccess( URLHandler ):
    _relativeURL = "abstractManagment.py/directAccess"


class UHAbstractToXML( URLHandler ):
    _relativeURL = "abstractManagment.py/xml"


class UHAbstractSubmissionDisplay( URLHandler ):
    _relativeURL = "abstractSubmission.py"


class UHAbstractCheckUser( URLHandler ):
    _relativeURL = "abstractSubmission.py/checkUser"


class UHAbstractAuthenticateUser( URLHandler ):
    _relativeURL = "abstractSubmission.py/authenticateUser"


class UHAbstractSubmissionSendLogin( URLHandler ):
    _relativeURL = "abstractSubmission.py/sendLogin"


class UHAbstractSubmissionAbstract( URLHandler ):
    _relativeURL = "abstractSubmission.py/submitAbstract"


class UHAbstractSubmitAuthors( URLHandler ):
    _relativeURL = "abstractSubmission.py/submitAuthors"


class UHAbstractSubmissionSelectAuthors( URLHandler ):
    _relativeURL = "abstractSubmission.py/selectAuthors"


class UHAbstractSubmissionAddAuthors( URLHandler ):
    _relativeURL = "abstractSubmission.py/addAuthors"


class UHAbstractSubmissionRemoveAuthors( URLHandler ):
    _relativeURL = "abstractSubmission.py/removeAuthors"


class UHAbstractSubmissionSelectPrimAuthor( URLHandler ):
    _relativeURL = "abstractSubmission.py/selectPrimAuthor"


class UHAbstractSubmissionSetPrimAuthor( URLHandler ):
    _relativeURL = "abstractSubmission.py/setPrimAuthor"


class UHAbstractSubmissionSelectSpeakers( URLHandler ):
    _relativeURL = "abstractSubmission.py/selectSpeakers"


class UHAbstractSubmissionAddSpeakers( URLHandler ):
    _relativeURL = "abstractSubmission.py/addSpeakers"


class UHAbstractSubmissionRemoveSpeakers( URLHandler ):
    _relativeURL = "abstractSubmission.py/removeSpeakers"


class UHAbstractSubmissionFinal( URLHandler ):
    _relativeURL = "abstractSubmission.py/final"


class UHAbstractCheckAbstract( URLHandler ):
    _relativeURL = "abstractSubmission.py/checkAbstract"


class UHAbstractModification( URLHandler ):
    _relativeURL = "abstractModification.py"


class UHAbstractModificationModify( URLHandler ):
    _relativeURL = "abstractModification.py/modify"


class UHAbstractModificationPerformModify( URLHandler ):
    _relativeURL = "abstractModification.py/performModify"


class UHAbstractModificationSelectAuthors( URLHandler ):
    _relativeURL = "abstractModification.py/selectAuthors"


class UHAbstractModificationAddAuthors( URLHandler ):
    _relativeURL = "abstractModification.py/addAuthors"


class UHAbstractModificationRemoveAuthors( URLHandler ):
    _relativeURL = "abstractModification.py/removeAuthors"


class UHAbstractModificationSelectSpeakers( URLHandler ):
    _relativeURL = "abstractModification.py/selectSpeakers"


class UHAbstractModificationAddSpeakers( URLHandler ):
    _relativeURL = "abstractModification.py/addSpeakers"


class UHAbstractModificationRemoveSpeakers( URLHandler ):
    _relativeURL = "abstractModification.py/removeSpeakers"


class UHConfAddTrack( URLHandler ):
    _relativeURL = "confModifProgram.py/addTrack"


class UHConfDelTracks( URLHandler ):
    _relativeURL = "confModifProgram.py/deleteTracks"


class UHConfPerformAddTrack( URLHandler ):
    _relativeURL = "confModifProgram.py/performAddTrack"


class UHTrackModification( URLHandler ):
    _relativeURL = "trackModification.py"


class UHTrackModifAbstracts( URLHandler ):
    _relativeURL = "trackModifAbstracts.py"



class UHTrackAbstractBase( URLHandler ):

    def getURL( cls, track, abstract ):
        url = cls._getURL()
        url.setParams( track.getLocator() )
        url.addParam( "abstractId", abstract.getId() )
        return url
    getURL = classmethod( getURL )


class UHTrackAbstractModif( UHTrackAbstractBase ):
    _relativeURL = "trackAbstractModif.py"


class UHAbstractTrackManagerDisplayPDF( UHTrackAbstractBase ):
    _relativeURL = "trackAbstractModif.py/abstractToPDF"


class UHAbstractsTrackManagerAction( URLHandler ):
    _relativeURL = "trackAbstractModif.py/abstractAction"


class UHTrackAbstractPropToAcc( UHTrackAbstractBase ):
    _relativeURL = "trackAbstractModif.py/proposeToBeAcc"


class UHTrackAbstractPropToRej( UHTrackAbstractBase ):
    _relativeURL = "trackAbstractModif.py/proposeToBeRej"


class UHTrackAbstractDirectAccess( URLHandler ):
    _relativeURL = "trackAbstractModif.py/directAccess"


class UHTrackAbstractPropForOtherTrack( UHTrackAbstractBase ):
    _relativeURL = "trackAbstractModif.py/proposeForOtherTracks"


class UHTrackModifCoordination( URLHandler ):
    _relativeURL = "trackModifCoordination.py"


class UHTrackSelectCoordinators( URLHandler ):
    _relativeURL = "trackModifCoordination.py/selectCoordinators"


class UHTrackAddCoordinators( URLHandler ):
    _relativeURL = "trackModifCoordination.py/addCoordinators"


class UHTrackRemoveCoordinators( URLHandler ):
    _relativeURL = "trackModifCoordination.py/removeCoordinators"


class UHTrackModifSubTrack( URLHandler ):
    _relativeURL = "trackModification.py/subTrack"


class UHSubTrackPerformDataModification( URLHandler ):
    _relativeURL = "trackModification.py/subTrackPerformModify"


class UHSubTrackDataModif( URLHandler ):
    _relativeURL = "trackModification.py/modifySubTrack"

class UHTrackDataModif( URLHandler ):
    _relativeURL = "trackModification.py/modify"


class UHTrackPerformDataModification( URLHandler ):
    _relativeURL = "trackModification.py/performModify"


class UHTrackDeleteSubTracks( URLHandler ):
    _relativeURL = "trackModification.py/deleteSubTracks"


class UHTrackAddSubTracks( URLHandler ):
    _relativeURL = "trackModification.py/addSubTrack"


class UHTrackPerformAddSubTrack( URLHandler ):
    _relativeURL = "trackModification.py/performAddSubTrack"


class UHTrackAbstractModIntComments(UHTrackAbstractBase):
    _relativeURL = "trackAbstractModif.py/comments"


class UHConfModifSchedule( URLHandler ):
    _relativeURL = "confModifSchedule.py"

class UHConfModifScheduleCustomizePDF( URLHandler ):
    _relativeURL = "confModifSchedule.py/customizePdf"


##class UHConfModifScheduleGraphic( URLHandler ):
##    _relativeURL = "confModifSchedule.py/graphic"


class UHConfModifScheduleEntries( URLHandler ):
    _relativeURL = "confModifSchedule.py/entries"


class UHConfModifScheduleEntriesRemove( URLHandler ):
    _relativeURL = "confModifSchedule.py/removeEntries"


class UHConfModifScheduleRelocate( URLHandler ):
    _relativeURL = "confModifSchedule.py/relocate"


class UHConfDelSchItems( URLHandler ):
    _relativeURL = "confModifSchedule.py/deleteItems"


#class UHConfModSchEditBreak( URLHandler ):
#    _relativeURL = "confModifSchedule.py/editBreak"


class UHConfModSchEditContrib(URLHandler):
    _relativeURL = "confModifSchedule.py/editContrib"


class UHConfModSchEditSlot(URLHandler):
    _relativeURL = "confModifSchedule.py/editSlot"



class UHConfAddSession( URLHandler ):
    _relativeURL = "confModifSchedule.py/addSession"

class UHConfPerformAddSession( URLHandler ):
    _relativeURL = "confModifSchedule.py/performAddSession"

class UHConfNewSessionConvenerSearch(URLHandler):
    _relativeURL = "sessionCreation.py/convenerSearch"

class UHConfNewSessionConvenerNew(URLHandler):
    _relativeURL = "sessionCreation.py/convenerNew"

class UHConfNewSessionPersonAdd(URLHandler):
    _relativeURL = "sessionCreation.py/personAdd"

class UHSessionDataModificationConvenerSearch(URLHandler):
    _relativeURL = "sessionModification.py/convenerSearch"

class UHSessionDataModificationConvenerNew(URLHandler):
    _relativeURL = "sessionModification.py/convenerNew"

class UHSessionDataModificationPersonAdd(URLHandler):
    _relativeURL = "sessionModification.py/personAdd"

class UHSessionDataModificationNewConvenerSearch(URLHandler):
    _relativeURL = "sessionModification.py/newConvenerSearch"

class UHSessionDataModificationNewConvenerCreate(URLHandler):
    _relativeURL = "sessionModification.py/newConvenerCreate"

class UHSessionDataModificationConvenerAdd(URLHandler):
    _relativeURL = "sessionModification.py/convenerAdd"

class UHConfAddContribution( URLHandler ):
    _relativeURL = "confModifContribList.py/addContribution"

class UHConfPerformAddContribution( URLHandler ):
    _relativeURL = "confModifContribList.py/performAddContribution"

class UHMConfPerformAddContribution( URLHandler ):
    _relativeURL = "confModifContribList.py/performAddContributionM"


class UHContribConfSelectionAction( URLHandler ):
    _relativeURL = "confModifContribList.py/contribsActions"


class UHContribsConfManagerDisplayPDF( URLHandler ):
    _relativeURL = "confModifContribList.py/contribsToPDF"

class UHContribsConfManagerDisplayMenuPDF( URLHandler ):
    _relativeURL = "confModifContribList.py/contribsToPDFMenu"


class UHContribsConfManagerDisplayParticipantList( URLHandler ):
    _relativeURL = "confModifContribList.py/participantList"

#class UHContribsConfManagerDisplayXML( URLHandler ):
#    _relativeURL = "abstractsManagment.py/abstractsToXML"

class UHConfAddBreak( URLHandler ):
    _relativeURL = "confModifSchedule.py/addBreak"


class UHConfPerformAddBreak( URLHandler ):
    _relativeURL = "confModifSchedule.py/performAddBreak"


class UHConfModifyBreak( URLHandler ):
    _relativeURL = "confModifSchedule.py/modifyBreak"

class UHSessionModifyBreak( URLHandler ):
    _relativeURL = "sessionModifSchedule.py/modifyBreak"


class UHConfPerformModifyBreak( URLHandler ):
    _relativeURL = "confModifSchedule.py/performModifyBreak"

class UHSessionPerformModifyBreak( URLHandler ):
    _relativeURL = "sessionModifSchedule.py/performModifyBreak"


class UHSessionClose( URLHandler ):
    _relativeURL = "sessionModification.py/close"


class UHSessionOpen( URLHandler ):
    _relativeURL = "sessionModification.py/open"


class UHSessionCreation( URLHandler ):
    _relativeURL = "confModifSchedule.py"


class UHContribCreation( URLHandler ):
    _relativeURL = "confModifSchedule.py"


class UHContribToXMLConfManager( URLHandler ):
    _relativeURL = "contributionModification.py/xml"


class UHContribToXML( URLHandler ):
    _relativeURL = "contributionDisplay.py/xml"


class UHContribToiCal( URLHandler ):
    _relativeURL = "contributionDisplay.py/ical"


class UHContribToPDFConfManager( URLHandler ):
    _relativeURL = "contributionModification.py/pdf"


class UHContribToPDF( URLHandler ):
    _relativeURL = "contributionDisplay.py/pdf"


class UHContribModifAC( URLHandler ):
    _relativeURL = "contributionAC.py"


class UHContributionSelectManagers( URLHandler ):
    _relativeURL = "contributionAC.py/selectManagers"


class UHContributionAddManagers( URLHandler ):
    _relativeURL = "contributionAC.py/addManagers"


class UHContributionRemoveManagers( URLHandler ):
    _relativeURL = "contributionAC.py/removeManagers"


class UHContributionSetVisibility( URLHandler ):
    _relativeURL = "contributionAC.py/setVisibility"


class UHContributionSelectAllowed( URLHandler ):
    _relativeURL = "contributionAC.py/selectAllowedToAccess"


class UHContributionAddAllowed( URLHandler ):
    _relativeURL = "contributionAC.py/addAllowedToAccess"


class UHContributionRemoveAllowed( URLHandler ):
    _relativeURL = "contributionAC.py/removeAllowedToAccess"


class UHContribModSubmittersRem(URLHandler):
    _relativeURL = "contributionAC.py/removeSubmitters"


class UHContribModSubmittersSel(URLHandler):
    _relativeURL = "contributionAC.py/selectSubmitters"


class UHContribModSubmittersAdd(URLHandler):
    _relativeURL = "contributionAC.py/addSubmitters"

class UHContributionAddSpeakers( URLHandler ):
    _relativeURL = "contributionModification.py/addSpeakers"

class UHContribModifMaterialMgmt( URLHandler ):
    _relativeURL = "contributionModification.py/materials"

class UHContribModifAddMaterials( URLHandler ):
    _relativeURL = "contributionModification.py/materialsAdd"

class UHContributionRemoveMaterials( URLHandler ):
    _relativeURL = "contributionModification.py/removeMaterials"

# <Deprecated>
class UHContributionAddMaterial( URLHandler ):
    _relativeURL = "contributionModification.py/addMaterial"

class UHContributionPerformAddMaterial( URLHandler ):
    _relativeURL = "contributionModification.py/performAddMaterial"
# </Deprecated>

class UHContributionSelectSpeakers( URLHandler ):
    _relativeURL = "contributionModification.py/selectSpeakers"


class UHContributionRemoveSpeakers( URLHandler ):
    _relativeURL = "contributionModification.py/removeSpeakers"


class UHContributionAddDomain( URLHandler ):
    _relativeURL = "contributionAC.py/addDomains"


class UHContributionRemoveDomain( URLHandler ):
    _relativeURL = "contributionAC.py/removeDomains"


class UHContribModifSubCont( URLHandler ):
    _relativeURL = "contributionModifSubCont.py"


class UHContribDeleteSubCont( URLHandler ):
    _relativeURL = "contributionModifSubCont.py/delete"


class UHContribAddSubCont( URLHandler ):
    _relativeURL = "contributionModifSubCont.py/add"


class UHContribCreateSubCont( URLHandler ):
    _relativeURL = "contributionModifSubCont.py/create"


class UHContribCreateSubContPresenterSearch(URLHandler):
    _relativeURL = "contributionModifSubCont.py/presenterSearch"

class UHContribCreateSubContPresenterNew(URLHandler):
    _relativeURL = "contributionModifSubCont.py/presenterNew"

class UHContribCreateSubContPersonAdd(URLHandler):
    _relativeURL = "contributionModifSubCont.py/personAdd"


class UHContribUpSubCont( URLHandler ):
    _relativeURL = "contributionModifSubCont.py/up"


class UHContribDownSubCont( URLHandler ):
    _relativeURL = "contributionModifSubCont.py/Down"

class UHSubContribActions(URLHandler):
    _relativeURL ="contributionModifSubCont.py/actionSubContribs"


class UHContribModifTools( URLHandler ):
    _relativeURL = "contributionTools.py"


class UHContributionDataModif( URLHandler ):
    _relativeURL = "contributionModification.py/modifData"


class UHContributionDataModification( URLHandler ):
    _relativeURL = "contributionModification.py/data"


class UHContributionCreation( URLHandler ):
    _relativeURL = "contributionCreation.py"


class UHContributionReportNumberEdit( URLHandler ):
    _relativeURL = "contributionModification.py/editReportNumber"

class UHContributionReportNumberPerformEdit( URLHandler ):
    _relativeURL = "contributionModification.py/performEditReportNumber"

class UHContributionReportNumberRemove( URLHandler ):
    _relativeURL = "contributionModification.py/removeReportNumber"


class UHSubContributionCreation( URLHandler ):
    _relativeURL = "subContributionCreation.py"


class UHBreakCreation( URLHandler ):
    _relativeURL = "confModifSchedule.py"


class UHConfModifAC( URLHandler ):
    _relativeURL = "confModifAC.py"

class UHConfSetVisibility( URLHandler ):
    _relativeURL = "confModifAC.py/setVisibility"


class UHConfSetAccessKey( URLHandler ):
    _relativeURL = "confModifAC.py/setAccessKey"


class UHConfSetModifKey( URLHandler ):
    _relativeURL = "confModifAC.py/setModifKey"


class UHConfSelectAllowed( URLHandler ):
    _relativeURL = "confModifAC.py/selectAllowed"


class UHConfAddAllowed( URLHandler ):
    _relativeURL = "confModifAC.py/addAllowed"


class UHConfRemoveAllowed( URLHandler ):
    _relativeURL = "confModifAC.py/removeAllowed"


class UHConfAddDomain( URLHandler ):
    _relativeURL = "confModifAC.py/addDomains"


class UHConfRemoveDomain( URLHandler ):
    _relativeURL = "confModifAC.py/removeDomains"


class UHConfSelectManagers( URLHandler ):
    _relativeURL = "confModifAC.py/selectManagers"

class UHConfAddManagers( URLHandler ):
    _relativeURL = "confModifAC.py/addManagers"

class UHConfGrantSubmissionToAllSpeakers( URLHandler ):
    _relativeURL = "confModifAC.py/grantSubmissionToAllSpeakers"

class UHConfRemoveManagers( URLHandler ):
    _relativeURL = "confModifAC.py/removeManagers"

class UHConfRemoveAllSubmissionRights( URLHandler ):
    _relativeURL = "confModifAC.py/removeAllSubmissionRights"

class UHConfGrantModificationToAllConveners( URLHandler ):
    _relativeURL = "confModifAC.py/grantModificationToAllConveners"

class UHConfModifCoordinatorRights(URLHandler):
    _relativeURL = "confModifAC.py/modifySessionCoordRights"

## Old Videoconference related
class UHBookingsVRVS( URLHandler ):
    _relativeURL = "confModifBookings.py/createBookingVRVS"


class UHPerformBookingsVRVS( URLHandler ):
    _relativeURL = "confModifBookings.py/performBookingVRVS"


class UHBookingDetail(URLHandler):
    _relativeURL = "confModifBookings.py/BookingDetail"


class UHBookingsHERMES( URLHandler ):
    _relativeURL = "confModifBookings.py/createBookingHERMES"


class UHHERMESParticipantCreation( URLHandler ):
    _relativeURL = "ConferenceModifBookings.py/addHERMESParticipant"


class UHPerformBookingsHERMES( URLHandler ):
    _relativeURL = "confModifBookings.py/performBookingHERMES"


class UHConfModifBookings( URLHandler ):
    _relativeURL = "confModifBookings.py"


class UHConfModifBookingList( URLHandler ):
    _relativeURL = "confModifBookings.py/index"


class UHConfModifBookingAction( URLHandler ):
    _relativeURL = "confModifBookings.py/performBookingAction"


class UHConfModifBookingPerformDeletion( URLHandler ):
    _relativeURL = "confModifBookings.py/performBookingDeletion"


class UHConfModifBookingModification(URLHandler):
    _relativeURL = "confModifBookings.py/performBookingModification"
## End of old Videoconference related


## New Collaboration related
class UHAdminCollaboration(URLHandler):
    _relativeURL = "adminCollaboration.py"

class UHConfModifCollaboration(OptionallySecureURLHandler):
    _relativeURL = "confModifCollaboration.py"

class UHConfModifCollaborationManagers(URLHandler):
    _relativeURL = "confModifCollaboration.py/managers"

class UHCollaborationDisplay(URLHandler):
    _relativeURL = "collaborationDisplay.py"

## End of new Collaboration related

class UHConfModifTools( URLHandler ):
    _relativeURL = "confModifTools.py"

class UHConfModifListings( URLHandler ):
    _relativeURL = "confModifListings.py"

class UHConfModifParticipants( URLHandler ):
    _relativeURL = "confModifParticipants.py"

class UHConfModifLog( URLHandler ):
    _relativeURL = "confModifLog.py"

class UHConfModifLogItem( URLHandler ):
    _relativeURL = "confModifLog.py/logItem"

class UHInternalPageDisplay( URLHandler ):
    _relativeURL = "internalPage.py"

class UHConfModifDisplay( URLHandler ):
    _relativeURL = "confModifDisplay.py"

class UHConfModifDisplayCustomization( URLHandler ):
    _relativeURL = "confModifDisplay.py/custom"

class UHConfModifDisplayMenu( URLHandler ):
    _relativeURL = "confModifDisplay.py/menu"

class UHConfModifDisplayResources( URLHandler ):
    _relativeURL = "confModifDisplay.py/resources"

class UHConfModifDisplayConfHeader( URLHandler ):
    _relativeURL = "confModifDisplay.py/confHeader"

class UHConfModifDisplayLink( URLHandler ):
    _relativeURL = "confModifDisplay.py/modifyLink"


class UHConfModifDisplayAddLink( URLHandler ):
    _relativeURL = "confModifDisplay.py/addLink"

class UHConfModifDisplayAddPage( URLHandler ):
    _relativeURL = "confModifDisplay.py/addPage"

class UHConfModifDisplayAddPageFile( URLHandler ):
    _relativeURL = "confModifDisplay.py/addPageFile"

class UHConfModifDisplayAddPageFileBrowser( URLHandler ):
    _relativeURL = "confModifDisplay.py/addPageFileBrowser"

class UHConfModifDisplayModifyData( URLHandler ):
    _relativeURL = "confModifDisplay.py/modifyData"

class UHConfModifDisplayModifySystemData( URLHandler ):
    _relativeURL = "confModifDisplay.py/modifySystemData"

class UHConfModifDisplayAddSpacer( URLHandler ):
    _relativeURL = "confModifDisplay.py/addSpacer"


class UHConfModifDisplayRemoveLink( URLHandler ):
    _relativeURL = "confModifDisplay.py/removeLink"


class UHConfModifDisplayToggleLinkStatus( URLHandler ):
    _relativeURL = "confModifDisplay.py/toggleLinkStatus"

class UHConfModifDisplayToggleHomePage( URLHandler ):
    _relativeURL = "confModifDisplay.py/toggleHomePage"

class UHConfModifDisplayUpLink( URLHandler ):
    _relativeURL = "confModifDisplay.py/upLink"


class UHConfModifDisplayDownLink( URLHandler ):
    _relativeURL = "confModifDisplay.py/downLink"

class UHConfModifFormatTitleBgColor( URLHandler ):
    _relativeURL = "confModifDisplay.py/formatTitleBgColor"

class UHConfModifFormatTitleTextColor( URLHandler ):
    _relativeURL = "confModifDisplay.py/formatTitleTextColor"

class UHConfDeletion( URLHandler ):
    _relativeURL = "confModifTools.py/delete"


class UHConfClone( URLHandler ):
    _relativeURL = "confModifTools.py/clone"

class UHConfPerformCloning( URLHandler ):
    _relativeURL = "confModifTools.py/performCloning"

class UHConfPerformCloneOnce( URLHandler ):
    _relativeURL = "confModifTools.py/performCloneOnce"


class UHConfPerformCloneInterval( URLHandler ):
    _relativeURL = "confModifTools.py/performCloneInterval"


class UHConfPerformCloneDays( URLHandler ):
    _relativeURL = "confModifTools.py/performCloneDays"

class UHConfAllSessionsConveners( URLHandler ):
    _relativeURL = "confModifTools.py/allSessionsConveners"

class UHConfAllSessionsConvenersAction( URLHandler ):
    _relativeURL = "confModifTools.py/allSessionsConvenersAction"

class UHConfAllSpeakers( URLHandler ):
    _relativeURL = "confModifListings.py/allSpeakers"

class UHConfAllSpeakersAction( URLHandler ):
    _relativeURL = "confModifListings.py/allSpeakersAction"

class UHConfAllPrimaryAuthors( URLHandler ):
    _relativeURL = "confModifListings.py/allPrimaryAuthors"

class UHConfAllPrimaryAuthorsAction( URLHandler ):
    _relativeURL = "confModifListings.py/allPrimaryAuthorsAction"

class UHConfAllCoAuthors( URLHandler ):
    _relativeURL = "confModifListings.py/allCoAuthors"

class UHConfAllCoAuthorsAction( URLHandler ):
    _relativeURL = "confModifListings.py/allCoAuthorsAction"

class UHConfDisplayAlarm( URLHandler ):
    _relativeURL = "confModifTools.py/displayAlarm"

class UHConfAddAlarm( URLHandler ):
    _relativeURL = "confModifTools.py/addAlarm"


class UHSaveAlarm( URLHandler ):
    _relativeURL = "confModifTools.py/saveAlarm"


class UHTestSendAlarm( URLHandler ):
    _relativeURL = "confModifTools.py/testSendAlarm"


class UHSendAlarmNow( URLHandler ):
    _relativeURL = "confModifTools.py/sendAlarmNow"


class UHConfDeleteAlarm( URLHandler ):
    _relativeURL = "confModifTools.py/deleteAlarm"


class UHConfModifyAlarm( URLHandler ):
    _relativeURL = "confModifTools.py/modifyAlarm"


class UHConfSaveAlarm( URLHandler ):
    _relativeURL = "confModifTools.py/saveAlarm"


class UHSaveLogo( URLHandler ):
    _relativeURL = "confModifDisplay.py/saveLogo"


class UHRemoveLogo( URLHandler ):
    _relativeURL = "confModifDisplay.py/removeLogo"

class UHSaveCSS( URLHandler ):
    _relativeURL = "confModifDisplay.py/saveCSS"

class UHUseCSS( URLHandler ):
    _relativeURL = "confModifDisplay.py/useCSS"

class UHRemoveCSS( URLHandler ):
    _relativeURL = "confModifDisplay.py/removeCSS"

class UHSavePic( URLHandler ):
    _relativeURL = "confModifDisplay.py/savePic"

class UHConfModifParticipantsObligatory( URLHandler ):
    _relativeURL = "confModifParticipants.py/obligatory"

class UHConfModifParticipantsDisplay( URLHandler ):
    _relativeURL = "confModifParticipants.py/display"

class UHConfModifParticipantsAddedInfo( URLHandler ):
    _relativeURL = "confModifParticipants.py/addedInfo"

class UHConfModifParticipantsAllowForApplying( URLHandler ):
    _relativeURL = "confModifParticipants.py/allowForApplying"

class UHConfModifParticipantsToggleAutoAccept( URLHandler ):
    _relativeURL = "confModifParticipants.py/toggleAutoAccept"

class UHConfModifParticipantsPending( URLHandler ):
    _relativeURL = "confModifParticipants.py/pendingParticipants"


class UHConfModifParticipantsAction( URLHandler ):
    _relativeURL = "confModifParticipants.py/action"


class UHConfModifParticipantsStatistics( URLHandler ):
    _relativeURL = "confModifParticipants.py/statistics"


class UHConfModifParticipantsSelectToAdd( URLHandler ):
    _relativeURL = "confModifParticipants.py/selectToAdd"


class UHConfModifParticipantsAddSelected( URLHandler ):
    _relativeURL = "confModifParticipants.py/addSelected"


class UHConfModifParticipantsNewToAdd( URLHandler ):
    _relativeURL = "confModifParticipants.py/newToAdd"


class UHConfModifParticipantsAddNew( URLHandler ):
    _relativeURL = "confModifParticipants.py/addNew"


class UHConfModifParticipantsSelectToInvite( URLHandler ):
    _relativeURL = "confModifParticipants.py/selectToInvite"


class UHConfModifParticipantsInviteSelected( URLHandler ):
    _relativeURL = "confModifParticipants.py/inviteSelected"


class UHConfModifParticipantsNewToInvite( URLHandler ):
    _relativeURL = "confModifParticipants.py/newToInvite"


class UHConfModifParticipantsInviteNew( URLHandler ):
    _relativeURL = "confModifParticipants.py/inviteNew"


class UHConfModifParticipantsDetails( URLHandler ):
    _relativeURL = "confModifParticipants.py/details"


class UHConfModifParticipantsEdit( URLHandler ):
    _relativeURL = "confModifParticipants.py/edit"


class UHConfModifParticipantsPendingAction( URLHandler ):
    _relativeURL = "confModifParticipants.py/pendingAction"


class UHConfModifParticipantsPendingDetails( URLHandler ):
    _relativeURL = "confModifParticipants.py/pendingDetails"


class UHConfModifParticipantsPendingEdit( URLHandler ):
    _relativeURL = "confModifParticipants.py/pendingEdit"


class UHConfParticipantsNewPending( URLHandler ):
    _relativeURL = "confModifParticipants.py/newPending"

class UHConfParticipantsAddPending( URLHandler ):
    _relativeURL = "confModifParticipants.py/addPending"


class UHConfParticipantsInvitation( URLHandler ):
    _relativeURL = "confModifParticipants.py/invitation"


class UHConfParticipantsRefusal( URLHandler ):
    _relativeURL = "confModifParticipants.py/refusal"


class UHConfModifParticipantsSendEmail( URLHandler ):
    _relativeURL = "confModifParticipants.py/sendEmail"

class UHConfModifToggleSearch( URLHandler ):
    _relativeURL = "confModifDisplay.py/toggleSearch"

class UHTickerTapeAction( URLHandler ):
    _relativeURL = "confModifDisplay.py/tickerTapeAction"

class UHUserManagement( URLHandler ):
    _relativeURL = "userManagement.py"

class UHUserManagementSwitchAuthorisedAccountCreation( URLHandler ):
    _relativeURL = "userManagement.py/switchAuthorisedAccountCreation"

class UHUserManagementSwitchNotifyAccountCreation( URLHandler ):
    _relativeURL = "userManagement.py/switchNotifyAccountCreation"

class UHUserManagementSwitchModerateAccountCreation( URLHandler ):
    _relativeURL = "userManagement.py/switchModerateAccountCreation"

class UHUsers( URLHandler ):
    _relativeURL = "userList.py"

class UHUserCreation( URLHandler ):
    _relativeURL = "userRegistration.py"

    def getURL( cls, returnURL="" ):
        if Config.getInstance().getRegistrationURL() != "":
            url = URL(Config.getInstance().getRegistrationURL())
        else:
            url = cls._getURL()
        if str(returnURL).strip() != "":
            url.addParam( "returnURL", returnURL )
        return url
    getURL = classmethod( getURL )

class UHUserPerformCreation( URLHandler ):
    _relativeURL = "userRegistration.py/update"

class UHUserMerge( URLHandler ):
    _relativeURL = "userMerge.py"

class UHLogMeAs( URLHandler ):
    _relativeURL = "userManagement.py/LogMeAs"

    def getURL( cls, returnURL="" ):
        url = cls._getURL()
        if str(returnURL).strip() != "":
            url.addParam( "returnURL", returnURL )
        return url
    getURL = classmethod( getURL )


class UHConfSignIn( URLHandler ):
    _relativeURL = "confLogin.py"

    def getURL( cls, conf, returnURL="" ):
        if Config.getInstance().getLoginURL().strip() != "":
            url = URL(Config.getInstance().getLoginURL())
        else:
            url = cls._getURL()
        url.setParams( conf.getLocator() )
        if str(returnURL).strip() != "":
            url.addParam( "returnURL", returnURL )
        return url
    getURL = classmethod( getURL )


class UHConfSignInAuthenticate( UHConfSignIn ):
    _relativeURL = "confLogin.py/signIn"


#class UHConfSignOut( URLHandler ):
#    _relativeURL = "confLogin.py/signOut"

class UHConfUserCreation( URLHandler ):
    _relativeURL = "confUser.py"

    def getURL( cls, conf, returnURL="" ):
        if Config.getInstance().getRegistrationURL().strip() != "":
            url = URL(Config.getInstance().getRegistrationURL())
        else:
            url = cls._getURL()
        url.setParams( conf.getLocator() )
        if str(returnURL).strip() != "":
            url.addParam( "returnURL", returnURL )
        return url
    getURL = classmethod( getURL )

class UHConfUser( URLHandler ):

    def getURL( cls, conference, av=None ):
        url = cls._getURL()
        loc = conference.getLocator().copy()
        if av:
            for i in av.getLocator().keys():
                loc[i] = av.getLocator()[i]
        url.setParams( loc )
        return url
    getURL = classmethod( getURL )


class UHConfDisabledAccount( UHConfUser ):
    _relativeURL = "confLogin.py/disabledAccount"


class UHConfUnactivatedAccount( UHConfUser ):
    _relativeURL = "confLogin.py/unactivatedAccount"


class UHConfUserCreated( UHConfUser ):
    _relativeURL = "confUser.py/created"


class UHConfSendLogin( UHConfUser ):
    _relativeURL = "confLogin.py/sendLogin"


class UHConfSendActivation( UHConfUser ):
    _relativeURL = "confLogin.py/sendActivation"


class UHConfUserExistWithIdentity( UHConfUser ):
    _relativeURL = "confUser.py/userExists"


class UHConfActiveAccount( UHConfUser ):
    _relativeURL = "confLogin.py/active"


class UHConfEnterAccessKey( UHConfUser ):
    _relativeURL = "conferenceDisplay.py/accessKey"

class UHConfForceEnterAccessKey( UHConfUser ):
    _relativeURL = "conferenceDisplay.py/forceAccessKey"

class UHConfManagementAccess(UHConfUser):
    _relativeURL = "conferenceModification.py/managementAccess"

class UHConfEnterModifKey( UHConfUser ):
    _relativeURL = "conferenceModification.py/modifKey"

class UHConfCloseModifKey( UHConfUser ):
    _relativeURL = "conferenceModification.py/closeModifKey"

class UHUserCreated( UHConfUser ):
    _relativeURL = "userRegistration.py/created"

class UHUserActive( URLHandler ):
    _relativeURL = "userRegistration.py/active"



class UHUserDetails( URLHandler ):
    _relativeURL = "userDetails.py"

class UHUserBaskets( URLHandler ):
    _relativeURL = "userBaskets.py"

class UHUserPreferences( URLHandler ):
    _relativeURL = "userPreferences.py"

class UHUserRegistration( URLHandler ):
    _relativeURL = "userRegistration.py"


class UHUserModification( URLHandler ):
    _relativeURL = "userRegistration.py/modify"


#class UHUserPerformModification( URLHandler ):
#    _relativeURL = "userRegistration.py/update"


class UHUserIdentityCreation( URLHandler ):
    _relativeURL = "identityCreation.py"


class UHUserRemoveIdentity( URLHandler ):
    _relativeURL = "identityCreation.py/remove"


class UHUserExistWithIdentity( UHConfUser ):
    _relativeURL = "userRegistration.py/UserExist"

class UHUserIdPerformCreation( URLHandler ):
    _relativeURL = "identityCreation.py/create"

class UHUserIdentityChangePassword( URLHandler ):
    _relativeURL = "identityCreation.py/changePassword"



class UHGroups( URLHandler ):
    _relativeURL = "groupList.py"


class UHNewGroup( URLHandler ):
    _relativeURL = "groupRegistration.py"

class UHNewLDAPGroup( URLHandler ):
    _relativeURL = "groupRegistration.py/LDAPGroup"


class UHGroupPerformRegistration( URLHandler ):
    _relativeURL = "groupRegistration.py/update"

class UHLDAPGroupPerformRegistration( URLHandler ):
    _relativeURL = "groupRegistration.py/updateLDAPGroup"


class UHGroupDetails( URLHandler ):
    _relativeURL = "groupDetails.py"


class UHGroupModification( URLHandler ):
    _relativeURL = "groupModification.py"


class UHGroupPerformModification( URLHandler ):
    _relativeURL = "groupModification.py/update"


class UHGroupSelectMembers( URLHandler ):
    _relativeURL = "groupDetails.py/selectMembers"


class UHGroupAddMembers( URLHandler ):
    _relativeURL = "groupDetails.py/addMembers"


class UHGroupRemoveMembers( URLHandler ):
    _relativeURL = "groupDetails.py/removeMembers"


class UHPrincipalDetails:

    def getURL( cls, member ):
        if isinstance( member, user.Group ):
            return UHGroupDetails.getURL( member )
        elif isinstance( member, user.Avatar ):
            return UHUserDetails.getURL( member )
        else:
            return ""
    getURL = classmethod( getURL )


class UHDomains( URLHandler ):
    _relativeURL = "domainList.py"


class UHNewDomain( URLHandler ):
    _relativeURL = "domainCreation.py"


class UHDomainPerformCreation( URLHandler ):
    _relativeURL = "domainCreation.py/create"


class UHDomainDetails( URLHandler ):
    _relativeURL = "domainDetails.py"


class UHDomainModification( URLHandler ):
    _relativeURL = "domainDataModification.py"


class UHDomainPerformModification( URLHandler ):
    _relativeURL = "domainDataModification.py/modify"

class UHRoomMappers( URLHandler ):
    _relativeURL = "roomMapper.py"


class UHNewRoomMapper( URLHandler ):
    _relativeURL = "roomMapper.py/creation"

class UHRoomMapperPerformCreation( URLHandler ):
    _relativeURL = "roomMapper.py/performCreation"


class UHRoomMapperDetails( URLHandler ):
    _relativeURL = "roomMapper.py/details"


class UHRoomMapperModification( URLHandler ):
    _relativeURL = "roomMapper.py/modify"


class UHRoomMapperPerformModification( URLHandler ):
    _relativeURL = "roomMapper.py/performModify"

class UHAdminArea( URLHandler ):
    _relativeURL = "adminList.py"

class UHAdminSwitchCacheActive( URLHandler ):
    _relativeURL = "adminList.py/switchCacheActive"

class UHAdminLocalDefinitions( URLHandler ):
    _relativeURL = "adminLocal.py"

class UHAdminSaveTemplateSet( URLHandler ):
    _relativeURL = "adminLocal.py/saveTemplateSet"

class UHAdminSwitchDebugActive( URLHandler ):
    _relativeURL = "adminList.py/switchDebugActive"

class UHAdminSwitchNewsActive( URLHandler ):
    _relativeURL = "adminList.py/switchNewsActive"

class UHAdminSwitchHighlightActive( URLHandler ):
    _relativeURL = "adminList.py/switchHighlightActive"

class UHAdminsSelectUsers( URLHandler ):
    _relativeURL = "adminList.py/selectAdmins"

class UHAdminsAddUsers( URLHandler ):
    _relativeURL = "adminList.py/addAdmins"

class UHAdminsRemoveUsers( URLHandler ):
    _relativeURL = "adminList.py/removeAdmins"

class UHAdminsStyles( URLHandler ):
    _relativeURL = "adminStyles.py"

class UHAdminsConferenceStyles( URLHandler ):
    _relativeURL = "adminConferenceStyles.py"

class UHAdminsAddStyle( URLHandler ):
    _relativeURL = "adminStyles.py/add"

class UHAdminsDeleteStyle( URLHandler ):
    _relativeURL = "adminStyles.py/delete"

class UHAdminsSystem( URLHandler ):
    _relativeURL = "adminSystem.py"

class UHAdminsSystemModif( URLHandler ):
    _relativeURL = "adminSystem.py/modify"

class UHMaterialModification( URLHandler ):

    @classmethod
    def getURL( cls, material, returnURL="" ):
        from MaKaC import conference

        owner = material.getOwner()

        # return handler depending on parent type
        if isinstance(owner, conference.Conference):
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


class UHMaterialModifyData( URLHandler ):
    _relativeURL = "materialModification.py/modify"

class UHMaterialPerformModifyData( URLHandler ):
    _relativeURL = "materialModification.py/performModify"


class UHMaterialRemoveResources( URLHandler ):
    _relativeURL = "materialModification.py/removeResources"


class UHMaterialLinkCreation( URLHandler ):
    _relativeURL = "materialModification.py/addLink"


class UHMaterialPerformLinkCreation( URLHandler ):
    _relativeURL = "materialModification.py/performAddLink"


class UHMaterialFileCreation( URLHandler ):
    _relativeURL = "materialModification.py/addFile"


class UHMaterialPerformFileCreation( URLHandler ):
    _relativeURL = "materialModification.py/performAddFile"


class UHMaterialModifAC( URLHandler ):
    _relativeURL = "materialModifAC.py"


class UHMaterialSetPrivacy( URLHandler ):
    _relativeURL = "materialModifAC.py/setPrivacy"

class UHMaterialSetVisibility( URLHandler ):
    _relativeURL = "materialModifAC.py/setVisibility"


class UHMaterialEnterAccessKey( URLHandler ):
    _relativeURL = "materialDisplay.py/accessKey"

class UHFileEnterAccessKey( URLHandler ):
    _relativeURL = "getFile.py/accessKey"

class UHMaterialSetAccessKey( URLHandler ):
    _relativeURL = "materialModifAC.py/setAccessKey"


class UHMaterialSelectAllowed( URLHandler ):
    _relativeURL = "materialModifAC.py/selectAllowed"


class UHMaterialAddAllowed( URLHandler ):
    _relativeURL = "materialModifAC.py/addAllowed"


class UHMaterialRemoveAllowed( URLHandler ):
    _relativeURL = "materialModifAC.py/removeAllowed"


class UHMaterialAddDomains( URLHandler ):
    _relativeURL = "materialModifAC.py/addDomains"


class UHMaterialRemoveDomains( URLHandler ):
    _relativeURL = "materialModifAC.py/removeDomains"


class UHFileModification( URLHandler ):
    _relativeURL = "fileModification.py"


class UHFileModifyData( URLHandler ):
    _relativeURL = "fileModification.py/modifyData"


class UHFilePerformModifyData( URLHandler ):
    _relativeURL = "fileModification.py/performModifyData"


class UHFileModifAC( URLHandler ):
    _relativeURL = "fileModifAC.py"


class UHFileSetVisibility( URLHandler ):
    _relativeURL = "fileModifAC.py/setVisibility"


class UHFileSelectAllowed( URLHandler ):
    _relativeURL = "fileModifAC.py/selectAllowed"


class UHFileAddAllowed( URLHandler ):
    _relativeURL = "fileModifAC.py/addAllowed"


class UHFileRemoveAllowed( URLHandler ):
    _relativeURL = "fileModifAC.py/removeAllowed"


class UHLinkModification( URLHandler ):
    _relativeURL = "linkModification.py"


class UHLinkModifyData( URLHandler ):
    _relativeURL = "linkModification.py/modifyData"


class UHLinkPerformModifyData( URLHandler ):
    _relativeURL = "linkModification.py/performModifyData"


class UHLinkModifAC( URLHandler ):
    _relativeURL = "linkModifAC.py"


class UHLinkSetVisibility( URLHandler ):
    _relativeURL = "linkModifAC.py/setVisibility"


class UHLinkSelectAllowed( URLHandler ):
    _relativeURL = "linkModifAC.py/selectAllowed"


class UHLinkAddAllowed( URLHandler ):
    _relativeURL = "linkModifAC.py/addAllowed"


class UHLinkRemoveAllowed( URLHandler ):
    _relativeURL = "linkModifAC.py/removeAllowed"


class UHCategoryModification( URLHandler ):
    _relativeURL = "categoryModification.py"

    def getActionURL( cls ):
        return ""
    getActionURL = classmethod( getActionURL )


class UHCategoryAddMaterial( URLHandler ):
    _relativeURL = "categoryFiles.py/addMaterial"

class UHCategoryActionSubCategs( URLHandler ):
    _relativeURL = "categoryModification.py/actionSubCategs"

class UHCategoryActionConferences( URLHandler ):
    _relativeURL = "categoryModification.py/actionConferences"

class UHCategoryClearCache( URLHandler ):
    _relativeURL = "categoryModification.py/clearCache"

class UHCategoryClearConferenceCaches( URLHandler ):
    _relativeURL = "categoryModification.py/clearConferenceCaches"

class UHCategModifAC( URLHandler ):
    _relativeURL = "categoryAC.py"

class UHCategorySetConfCreationControl( URLHandler ):
    _relativeURL = "categoryConfCreationControl.py/setCreateConferenceControl"

class UHCategorySetNotifyCreation( URLHandler ):
    _relativeURL = "categoryConfCreationControl.py/setNotifyCreation"

class UHCategorySelectConfCreators( URLHandler ):
    _relativeURL = "categoryConfCreationControl.py/selectAllowedToCreateConf"


class UHCategoryAddConfCreators( URLHandler ):
    _relativeURL = "categoryConfCreationControl.py/addAllowedToCreateConferences"


class UHCategoryRemoveConfCreators( URLHandler ):
    _relativeURL = "categoryConfCreationControl.py/removeAllowedToCreateConferences"


class UHCategModifTools( URLHandler ):
    _relativeURL = "categoryTools.py"

class UHCategoryDeletion( URLHandler ):
    _relativeURL = "categoryTools.py/delete"


class UHCategModifTasks( URLHandler ):
    _relativeURL = "categoryTasks.py"

class UHCategModifFiles( URLHandler ):
    _relativeURL = "categoryFiles.py"

class UHCategModifTasksAction( URLHandler ):
    _relativeURL = "categoryTasks.py/taskAction"

class UHCategoryDataModif( URLHandler ):
    _relativeURL = "categoryDataModification.py"


class UHCategoryPerformModification( URLHandler ):
    _relativeURL = "categoryDataModification.py/modify"


class UHCategoryTasksOption( URLHandler ):
    _relativeURL = "categoryDataModification.py/tasksOption"


class UHCategorySelectManagers( URLHandler ):
    _relativeURL = "categoryAC.py/selectManagers"


class UHCategoryAddManagers( URLHandler ):
    _relativeURL = "categoryAC.py/addManagers"


class UHCategoryRemoveManagers( URLHandler ):
    _relativeURL = "categoryAC.py/removeManagers"


class UHCategorySetVisibility( URLHandler ):
    _relativeURL = "categoryAC.py/setVisibility"


class UHCategorySelectAllowed( URLHandler ):
    _relativeURL = "categoryAC.py/selectAllowedToAccess"


class UHCategoryAddAllowed( URLHandler ):
    _relativeURL = "categoryAC.py/addAllowedToAccess"


class UHCategoryRemoveAllowed( URLHandler ):
    _relativeURL = "categoryAC.py/removeAllowedToAccess"


class UHCategoryAddDomain( URLHandler ):
    _relativeURL = "categoryAC.py/addDomains"


class UHCategoryRemoveDomain( URLHandler ):
    _relativeURL = "categoryAC.py/removeDomains"


class UHCategoryCreation( URLHandler ):
    _relativeURL = "categoryCreation.py"


class UHCategoryPerformCreation( URLHandler ):
    _relativeURL = "categoryCreation.py/create"


class UHCategoryDisplay( URLHandler ):
    _relativeURL = "categoryDisplay.py"

    def getURL( cls, target=None ):
        url = cls._getURL()
        if target:
            if target.isRoot():
                return UHWelcome.getURL()
            url.setParams( target.getLocator() )
        return url
    getURL = classmethod( getURL )


class UHCategoryMap( URLHandler ):
    _relativeURL = "categoryMap.py"

class UHCategoryOverview( URLHandler ):
    _relativeURL = "categOverview.py"

    def getURLFromOverview( cls, ow ):
        url = cls.getURL()
        url.setParams( ow.getLocator() )
        return url
    getURLFromOverview = classmethod( getURLFromOverview )


class UHTaskList( URLHandler ):
    _relativeURL = "taskList.py"

class UHTaskListAction( URLHandler ):
    _relativeURL = "taskList.py/taskListAction"

class UHTaskNew( URLHandler ):
    _relativeURL = "taskList.py/newTask"

class UHTaskNewAdd( URLHandler ):
    _relativeURL = "taskList.py/addNewTask"

class UHTaskNewResponsibleSearch( URLHandler ):
    _relativeURL = "taskList.py/searchResponsible"

class UHTaskNewResponsibleNew( URLHandler ):
    _relativeURL = "taskList.py/newResponsible"

class UHTaskNewPersonAdd( URLHandler ):
    _relativeURL = "taskList.py/personAdd"

class UHTaskDetails( URLHandler ):
    _relativeURL = "taskList.py/taskDetails"

class UHTaskDetailsAction( URLHandler ):
    _relativeURL = "taskList.py/taskDetailsAction"

class UHTaskDetailsResponsibleSearch( URLHandler ):
    _relativeURL = "taskList.py/detailSearchResponsible"

class UHTaskDetailsResponsibleNew( URLHandler ):
    _relativeURL = "taskList.py/detailNewResponsible"

class UHTaskDetailsPersonAdd( URLHandler ):
    _relativeURL = "taskList.py/detailPersonAdd"


class UHTaskCommentNew( URLHandler ):
    _relativeURL = "taskList.py/commentNew"

class UHTaskCommentNewAction( URLHandler ):
    _relativeURL = "taskList.py/commentNewAction"

class UHGeneralInfoModification( URLHandler ):
    _relativeURL = "generalInfoModification.py"


class UHGeneralInfoPerformModification( URLHandler ):
    _relativeURL = "generalInfoModification.py/update"


class UHContributionDelete( URLHandler ):
    _relativeURL = "contributionTools.py/delete"

class UHContributionWriteMinutes( URLHandler ):
    _relativeURL = "contributionTools.py/writeMinutes"

class UHContributionDisplayWriteMinutes( URLHandler ):
    _relativeURL = "contributionDisplay.py/writeMinutes"

class UHSubContributionDataModification( URLHandler ):
    _relativeURL = "subContributionModification.py/data"

class UHSubContributionReportNumberEdit( URLHandler ):
    _relativeURL = "subContributionModification.py/editReportNumber"

class UHSubContributionReportNumberPerformEdit( URLHandler ):
    _relativeURL = "subContributionModification.py/performEditReportNumber"

class UHSubContributionReportNumberRemove( URLHandler ):
    _relativeURL = "subContributionModification.py/removeReportNumber"

class UHSubContributionDataModif( URLHandler ):
    _relativeURL = "subContributionModification.py/modifData"

class UHSubContributionDelete( URLHandler ):
    _relativeURL = "subContributionTools.py/delete"


class UHSubContributionWriteMinutes( URLHandler ):
    _relativeURL = "subContributionTools.py/writeMinutes"


class UHSubContributionAddMaterial( URLHandler ):
    _relativeURL = "subContributionModification.py/addMaterial"


class UHSubContributionPerformAddMaterial( URLHandler ):
    _relativeURL = "subContributionModification.py/performAddMaterial"


class UHSubContributionRemoveMaterials( URLHandler ):
    _relativeURL = "subContributionModification.py/removeMaterials"

class UHSubContribModifAddMaterials( URLHandler ):
    _relativeURL = "subContributionModification.py/materialsAdd"

class UHSubContributionSelectSpeakers( URLHandler ):
    _relativeURL = "subContributionModification.py/selectSpeakers"


class UHSubContributionAddSpeakers( URLHandler ):
    _relativeURL = "subContributionModification.py/addSpeakers"

class UHSubContributionNewSpeaker( URLHandler ):
    _relativeURL = "subContributionModification.py/newSpeaker"

class UHSubContributionRemoveSpeakers( URLHandler ):
    _relativeURL = "subContributionModification.py/removeSpeakers"


class UHSubContribModifTools( URLHandler ):
    _relativeURL = "subContributionTools.py"

class UHSubContribModPresenter( URLHandler ):
    _relativeURL = "subContributionModification.py/modPresenter"

    def getURL( cls, target=None ):
        url = cls._getURL()
        url.setParams(target.getSubContrib().getLocator())
        url.addParam("authorId",target.getId())
        return url
    getURL = classmethod( getURL )


class UHSessionModification( URLHandler ):
    _relativeURL = "sessionModification.py"

class UHSessionModifMaterials( URLHandler ):
    _relativeURL = "sessionModification.py/materials"

class UHSessionDataModification( URLHandler ):
    _relativeURL = "sessionModification.py/modify"

class UHSessionDatesModification( URLHandler ):
    _relativeURL = "sessionModification.py/modifyDates"

class UHSessionModConvenerNew( URLHandler ):
    _relativeURL = "sessionModification.py/newConvener"


class UHSessionModConvenersRem( URLHandler ):
    _relativeURL = "sessionModification.py/remConveners"


class UHSessionModConvenerEdit( URLHandler ):
    _relativeURL = "sessionModification.py/editConvener"


class UHSessionModSlotConvenerNew( URLHandler ):
    _relativeURL = "sessionModification.py/newSlotConvener"


class UHSessionModSlotConvenersRem( URLHandler ):
    _relativeURL = "sessionModification.py/remSlotConveners"


class UHSessionModSlotConvenerEdit( URLHandler ):
    _relativeURL = "sessionModification.py/editSlotConvener"


class UHSessionFitSlot( URLHandler ):
    _relativeURL = "sessionModifSchedule.py/fitSlot"


class UHReducedSessionScheduleAction( URLHandler ):
    _relativeURL = "sessionModifSchedule.py/reducedScheduleAction"


class UHSessionModifScheduleRelocate( URLHandler ):
    _relativeURL = "sessionModifSchedule.py/relocate"

# <Deprecated>
class UHSessionAddMaterial( URLHandler ):
    _relativeURL = "sessionModification.py/addMaterial"


class UHSessionPerformAddMaterial( URLHandler ):
    _relativeURL = "sessionModification.py/performAddMaterial"
# </Deprecated>

class UHSessionRemoveMaterials( URLHandler ):
    _relativeURL = "sessionModification.py/removeMaterials"

class UHSessionModifAddMaterials( URLHandler ):
    _relativeURL = "sessionModification.py/materialsAdd"


class UHSessionImportContrib( URLHandler ):
    _relativeURL = "sessionModification.py/importContrib"


class UHSessionModifSchedule( URLHandler ):
    _relativeURL = "sessionModifSchedule.py"


class UHSessionModFit( URLHandler ):
    _relativeURL = "sessionModifSchedule.py/fitSession"


class UHSessionModSchEditContrib(URLHandler):
    _relativeURL = "sessionModifSchedule.py/editContrib"


class UHSessionModSlotEdit( URLHandler ):
    _relativeURL = "sessionModifSchedule.py/slotEdit"


class UHSessionModSlotNew( URLHandler ):
    _relativeURL = "sessionModifSchedule.py/slotNew"


class UHSessionModSlotRem( URLHandler ):
    _relativeURL = "sessionModifSchedule.py/slotRem"

class UHSessionModSlotCalc( URLHandler ):
    _relativeURL = "sessionModifSchedule.py/slotCalc"

class UHSessionModSlotCompact( URLHandler ):
    _relativeURL = "sessionModifSchedule.py/slotCompact"


class UHSessionModSlotMoveUpEntry( URLHandler ):
    _relativeURL = "sessionModifSchedule.py/moveUpEntry"


class UHSessionModSlotMoveDownEntry( URLHandler ):
    _relativeURL = "sessionModifSchedule.py/moveDownEntry"


class UHSessionModScheduleDataEdit( URLHandler ):
    _relativeURL = "sessionModifSchedule.py/editData"


class UHSessionModScheduleAddContrib( URLHandler ):
    _relativeURL = "sessionModifSchedule.py/addContrib"

class UHSessionModScheduleNewContrib( URLHandler ):
    _relativeURL = "sessionModifSchedule.py/newContrib"

class UHSessionAddContribution( URLHandler ):
    _relativeURL = "sessionModifSchedule.py/addContrib"


class UHSessionPerformAddContribution( URLHandler ):
    _relativeURL = "sessionModifSchedule.py/performAddContrib"


class UHSessionAddBreak( URLHandler ):
    _relativeURL = "sessionModifSchedule.py/addBreak"

class UHSessionDelSchItems( URLHandler ):
    _relativeURL = "sessionModifSchedule.py/delItems"


class UHSessionModifAC( URLHandler ):
    _relativeURL = "sessionModifAC.py"


class UHSessionSetVisibility( URLHandler ):
    _relativeURL = "sessionModifAC.py/setVisibility"


class UHSessionSelectAllowed( URLHandler ):
    _relativeURL = "sessionModifAC.py/selectAllowed"


class UHSessionAddAllowed( URLHandler ):
    _relativeURL = "sessionModifAC.py/addAllowed"


class UHSessionRemoveAllowed( URLHandler ):
    _relativeURL = "sessionModifAC.py/removeAllowed"


class UHSessionAddDomains( URLHandler ):
    _relativeURL = "sessionModifAC.py/addDomains"


class UHSessionRemoveDomains( URLHandler ):
    _relativeURL = "sessionModifAC.py/removeDomains"


class UHSessionSelectManagers( URLHandler ):
    _relativeURL = "sessionModifAC.py/selectManagers"


class UHSessionAddManagers( URLHandler ):
    _relativeURL = "sessionModifAC.py/addManagers"


class UHSessionRemoveManagers( URLHandler ):
    _relativeURL = "sessionModifAC.py/removeManagers"


class UHSessionModifTools( URLHandler ):
    _relativeURL = "sessionModifTools.py"

class UHSessionModifComm( URLHandler ):
    _relativeURL = "sessionModifComm.py"

class UHSessionModifCommEdit( URLHandler ):
    _relativeURL = "sessionModifComm.py/edit"


class UHSessionDeletion( URLHandler ):
    _relativeURL = "sessionModifTools.py/delete"

class UHSessionWriteMinutes( URLHandler ):
    _relativeURL = "sessionModifTools.py/writeMinutes"

class UHContributionModification( URLHandler ):
    _relativeURL = "contributionModification.py"


class UHContribModifMaterials( URLHandler ):
    _relativeURL = "contributionModification.py/materials"

class UHContribModifSchedule( URLHandler ):
    _relativeURL = "contributionModification.py/schedule"

class UHContribModNewPrimAuthor( URLHandler ):
    _relativeURL = "contributionModification.py/newPrimAuthor"

class UHContribModPrimAuthSearch(URLHandler):
    _relativeURL = "contributionModification.py/searchPrimAuthor"

class UHContribModPrimAuthSearchAdd(URLHandler):
    _relativeURL = "contributionModification.py/searchAddPrimAuthor"

class UHContribModCoAuthSearch(URLHandler):
    _relativeURL = "contributionModification.py/searchCoAuthor"

class UHContribModCoAuthSearchAdd(URLHandler):
    _relativeURL = "contributionModification.py/searchAddCoAuthor"

class UHContribModPrimaryAuthorAction( URLHandler ):
    _relativeURL = "contributionModification.py/primaryAuthorAction"

class UHContribModRemPrimAuthors( URLHandler ):
    _relativeURL = "contributionModification.py/remPrimAuthors"


class UHContribModPrimAuthor( URLHandler ):
    _relativeURL = "contributionModification.py/modPrimAuthor"

    def getURL( cls, target=None ):
        url = cls._getURL()
        url.setParams(target.getContribution().getLocator())
        url.addParam("authorId",target.getId())
        return url
    getURL = classmethod( getURL )


class UHContribModNewCoAuthor( URLHandler ):
    _relativeURL = "contributionModification.py/newCoAuthor"

class UHContribModCoAuthorAction( URLHandler ):
    _relativeURL = "contributionModification.py/coAuthorAction"

class UHContribModRemCoAuthors( URLHandler ):
    _relativeURL = "contributionModification.py/remCoAuthors"


class UHContribModCoAuthor( URLHandler ):
    _relativeURL = "contributionModification.py/modCoAuthor"

    def getURL( cls, target=None ):
        url = cls._getURL()
        url.setParams(target.getContribution().getLocator())
        url.addParam("authorId",target.getId())
        return url
    getURL = classmethod( getURL )

class UHContribModNewSpeaker( URLHandler ):
    _relativeURL = "contributionModification.py/newSpeaker"

class UHContribModSpeaker( URLHandler ):
    _relativeURL = "contributionModification.py/modSpeaker"

    def getURL( cls, target=None ):
        url = cls._getURL()
        url.setParams(target.getContribution().getLocator())
        url.addParam("authorId",target.getId())
        return url
    getURL = classmethod( getURL )


class UHContributionMove( URLHandler ):
    _relativeURL = "contributionModification.py/move"


class UHContributionPerformMove( URLHandler ):
    _relativeURL = "contributionModification.py/performMove"


class UHSubContribModification( URLHandler ):
    _relativeURL = "subContributionModification.py"

class UHSubContribModifMaterials( URLHandler ):
    _relativeURL = "subContributionModification.py/materials"

class UHMaterialDisplay( URLHandler ):
    _relativeURL = "materialDisplay.py"

class UHConferenceProgram( URLHandler ):
    _relativeURL = "conferenceProgram.py"


class UHConferenceProgramPDF( URLHandler ):
    _relativeURL = "conferenceProgram.py/pdf"


class UHConferenceTimeTable( URLHandler ):
    _relativeURL = "conferenceTimeTable.py"


class UHConfTimeTablePDF( URLHandler ):
    _relativeURL = "conferenceTimeTable.py/pdf"


class UHConferenceCFA( URLHandler ):
    _relativeURL = "conferenceCFA.py"


class UHSessionDisplay( URLHandler ):
    _relativeURL = "sessionDisplay.py"

class UHSessionDisplayWriteMinutes( URLHandler ):
    _relativeURL = "sessionDisplay.py/writeMinutes"

class UHSessionToiCal( URLHandler ):
    _relativeURL = "sessionDisplay.py/ical"

class UHContributionDisplay( URLHandler ):
    _relativeURL = "contributionDisplay.py"

class UHContributionDisplayRemoveMaterial( URLHandler ):
    _relativeURL = "contributionDisplay.py/removeMaterial"

class UHSubContributionDisplay( URLHandler ):
    _relativeURL = "subContributionDisplay.py"

class UHSubContributionDisplayWriteMinutes( URLHandler ):
    _relativeURL = "subContributionDisplay.py/writeMinutes"

class UHSubContributionModification( URLHandler ):
    _relativeURL = "subContributionModification.py"

class UHFileAccess( URLHandler ):
    _relativeURL = "getFile.py/access"

class UHVideoWmvAccess( URLHandler ):
    _relativeURL = "getFile.py/wmv"

class UHVideoFlashAccess( URLHandler ):
    _relativeURL = "getFile.py/flash"

class UHErrorReporting( URLHandler ):
    _relativeURL = "errors.py"

class UHErrorSendReport( URLHandler ):
    _relativeURL = "error.py/sendReport"

class UHAbstractWithdraw( URLHandler ):
    _relativeURL = "abstractWithdraw.py"


class UHAbstractRecovery( URLHandler ):
    _relativeURL = "abstractWithdraw.py/recover"


class UHConfModifContribList( URLHandler ):
    _relativeURL = "confModifContribList.py"

class UHConfModifContribListOpenMenu( URLHandler ):
    _relativeURL = "confModifContribList.py/openMenu"

class UHConfModifContribListCloseMenu( URLHandler ):
    _relativeURL = "confModifContribList.py/closeMenu"


class UHContribModAddSpeakers( URLHandler ):
    _relativeURL = "contributionModification.py/addSpk"


class UHContribModRemSpeakers( URLHandler ):
    _relativeURL = "contributionModification.py/remSpk"

class UHContribModSpeakerSearch( URLHandler ):
    _relativeURL = "contributionModification.py/searchSpk"

class UHContribModSpeakerSearchAdd(URLHandler):
    _relativeURL = "contributionModification.py/searchAddSpk"

class UHContribModSetTrack( URLHandler ):
    _relativeURL = "contributionModification.py/setTrack"


class UHContribModSetSession( URLHandler ):
    _relativeURL = "contributionModification.py/setSession"


class UHTrackModMoveUp( URLHandler ):
    _relativeURL = "confModifProgram.py/moveTrackUp"


class UHTrackModMoveDown( URLHandler ):
    _relativeURL = "confModifProgram.py/moveTrackDown"


class UHAbstractModAC( URLHandler ):
    _relativeURL = "abstractManagment.py/ac"


class UHAbstractModEditData(URLHandler):
    _relativeURL = "abstractManagment.py/editData"


class UHAbstractModIntComments(URLHandler):
    _relativeURL = "abstractManagment.py/comments"


class UHAbstractModNewIntComment(URLHandler):
    _relativeURL = "abstractManagment.py/newComment"


class UHAbstractModIntCommentEdit(URLHandler):
    _relativeURL = "abstractManagment.py/editComment"


class UHAbstractModIntCommentRem(URLHandler):
    _relativeURL = "abstractManagment.py/remComment"


class UHTrackAbstractModIntCommentNew(UHTrackAbstractBase):
    _relativeURL = "trackAbstractModif.py/commentNew"


class UHTrackAbstractModCommentBase( URLHandler ):

    def getURL( cls, track, comment):
        url = cls._getURL()
        url.setParams( comment.getLocator() )
        url.addParam( "trackId", track.getId() )
        return url
    getURL = classmethod( getURL )


class UHTrackAbstractModIntCommentEdit(UHTrackAbstractModCommentBase):
    _relativeURL = "trackAbstractModif.py/commentEdit"


class UHTrackAbstractModIntCommentRem(UHTrackAbstractModCommentBase):
    _relativeURL = "trackAbstractModif.py/commentRem"


class UHAbstractModNotifTplNew(URLHandler):
    _relativeURL = "confModifCFA.py/notifTplNew"


class UHAbstractModNotifTplRem(URLHandler):
    _relativeURL = "confModifCFA.py/notifTplRem"


class UHAbstractModNotifTplEdit(URLHandler):
    _relativeURL = "confModifCFA.py/notifTplEdit"


class UHAbstractModNotifTplDisplay(URLHandler):
    _relativeURL = "confModifCFA.py/notifTplDisplay"


class UHAbstractModNotifTplPreview(URLHandler):
    _relativeURL = "confModifCFA.py/notifTplPreview"


class UHTrackAbstractModMarkAsDup(UHTrackAbstractBase):
    _relativeURL = "trackAbstractModif.py/markAsDup"


class UHTrackAbstractModUnMarkAsDup(UHTrackAbstractBase):
    _relativeURL = "trackAbstractModif.py/unMarkAsDup"


class UHAbstractModMarkAsDup(URLHandler):
    _relativeURL = "abstractManagment.py/markAsDup"


class UHAbstractModUnMarkAsDup(URLHandler):
    _relativeURL = "abstractManagment.py/unMarkAsDup"


class UHAbstractModMergeInto(URLHandler):
    _relativeURL = "abstractManagment.py/mergeInto"


class UHAbstractModUnMerge(URLHandler):
    _relativeURL = "abstractManagment.py/unmerge"


class UHConfModNewAbstract(URLHandler):
    _relativeURL = "abstractsManagment.py/newAbstract"


class UHConfModNotifTplConditionNew(URLHandler):
    _relativeURL = "confModifCFA.py/notifTplCondNew"


class UHConfModNotifTplConditionRem(URLHandler):
    _relativeURL = "confModifCFA.py/notifTplCondRem"


class UHConfModifCFASelectSubmitter( URLHandler ):
    _relativeURL = "confModifCFA.py/selectSubmitter"


class UHConfModifCFAAddSubmitter( URLHandler ):
    _relativeURL = "confModifCFA.py/addSubmitter"


class UHConfModifCFARemoveSubmitter( URLHandler ):
    _relativeURL = "confModifCFA.py/removeSubmitter"


class UHAbstractChangeSubmitter( URLHandler ):
    _relativeURL = "abstractManagment.py/changeSubmitter"


class UHAbstractSetSubmitter( URLHandler ):
    _relativeURL = "abstractManagment.py/setSubmitter"


class UHConfModAbstractsMerge( URLHandler ):
    _relativeURL = "abstractsManagment.py/mergeAbstracts"


class UHAbstractModNotifLog( URLHandler ):
    _relativeURL = "abstractManagment.py/notifLog"

class UHAbstractModTools( URLHandler ):
    _relativeURL = "abstractTools.py"

class UHAbstractDelete( URLHandler ):
    _relativeURL = "abstractTools.py/delete"


class UHSessionModContribList( URLHandler ):
    _relativeURL = "sessionModification.py/contribList"


class UHSessionModContribListEditContrib( URLHandler ):
    _relativeURL = "sessionModification.py/editContrib"


class UHConfModScheduleAddContrib(URLHandler):
    _relativeURL = "confModifSchedule.py/addContrib"

class UHConfModScheduleNewContrib(URLHandler):
    _relativeURL = "confModifSchedule.py/newContrib"

class UHConfModSchedulePerformNewContrib(URLHandler):
    _relativeURL = "confModifSchedule.py/performNewContrib"

class UHConfModSchedulePresenterSearch(URLHandler):
    _relativeURL = "contributionCreation.py/presenterSearch"

class UHConfModSchedulePresenterNew(URLHandler):
    _relativeURL = "contributionCreation.py/presenterNew"

class UHConfModSchedulePersonAdd(URLHandler):
    _relativeURL = "contributionCreation.py/personAdd"

class UHConfModScheduleAuthorSearch(URLHandler):
    _relativeURL = "contributionCreation.py/authorSearch"

class UHConfModScheduleAuthorNew(URLHandler):
    _relativeURL = "contributionCreation.py/authorNew"

class UHConfModScheduleCoauthorSearch(URLHandler):
    _relativeURL = "contributionCreation.py/coauthorSearch"

class UHConfModScheduleCoauthorNew(URLHandler):
    _relativeURL = "contributionCreation.py/coauthorNew"

class UHConfModScheduleMoveEntryUp( URLHandler ):
    _relativeURL = "confModifSchedule.py/moveEntryUp"

class UHConfModScheduleMoveEntryDown( URLHandler ):
    _relativeURL = "confModifSchedule.py/moveEntryDown"

class UHConfModifReschedule( URLHandler ):
    _relativeURL = "confModifSchedule.py/reschedule"

class UHContributionList( URLHandler ):
    _relativeURL = "contributionListDisplay.py"

class UHContributionListAction( URLHandler ):
    _relativeURL = "contributionListDisplay.py/contributionsAction"

class UHContributionListToPDF( URLHandler ):
    _relativeURL = "contributionListDisplay.py/contributionsToPDF"

class UHConfModAbstractPropToAcc(URLHandler):
    _relativeURL="abstractManagment.py/propToAcc"

class UHAbstractManagmentBackToSubmitted(URLHandler):
    _relativeURL="abstractManagment.py/backToSubmitted"

class UHConfModAbstractPropToRej(URLHandler):
    _relativeURL="abstractManagment.py/propToRej"


class UHConfModAbstractWithdraw(URLHandler):
    _relativeURL="abstractManagment.py/withdraw"


class UHSessionModAddContribs( URLHandler ):
    _relativeURL = "sessionModification.py/addContribs"


class UHSessionModContributionAction( URLHandler ):
    _relativeURL = "sessionModification.py/contribAction"

class UHSessionModParticipantList( URLHandler ):
    _relativeURL = "sessionModification.py/participantList"

class UHSessionModToPDF( URLHandler ):
    _relativeURL = "sessionModification.py/contribsToPDF"

class UHConfModCFANotifTplUp(URLHandler):
    _relativeURL = "confModifCFA.py/notifTplUp"

class UHConfModCFANotifTplDown(URLHandler):
    _relativeURL = "confModifCFA.py/notifTplDown"

class UHConfAuthorIndex(URLHandler):
    _relativeURL = "confAuthorIndex.py"

class UHConfSpeakerIndex(URLHandler):
    _relativeURL = "confSpeakerIndex.py"

class UHContribModWithdraw( URLHandler ):
    _relativeURL = "contributionModification.py/withdraw"

class UHContribModPrimAuthUp( URLHandler ):
    _relativeURL = "contributionModification.py/primAuthUp"


class UHContribModPrimAuthDown( URLHandler ):
    _relativeURL = "contributionModification.py/primAuthDown"


class UHContribModCoAuthUp( URLHandler ):
    _relativeURL = "contributionModification.py/coAuthUp"


class UHContribModCoAuthDown( URLHandler ):
    _relativeURL = "contributionModification.py/coAuthDown"


class UHTrackModContribList(URLHandler):
    _relativeURL="trackModContribList.py"

class UHTrackModContributionAction( URLHandler ):
    _relativeURL = "trackModContribList.py/contribAction"

class UHTrackModParticipantList( URLHandler ):
    _relativeURL = "trackModContribList.py/participantList"

class UHTrackModToPDF( URLHandler ):
    _relativeURL = "trackModContribList.py/contribsToPDF"

class UHConfModContribQuickAccess(URLHandler):
    _relativeURL="confModifContribList.py/contribQuickAccess"


class UHSessionModContribQuickAccess(URLHandler):
    _relativeURL="sessionModification.py/contribQuickAccess"


class UHTrackModContribQuickAccess(URLHandler):
    _relativeURL="trackModContribList.py/contribQuickAccess"


class UHSessionModCoordinatorsRem(URLHandler):
    _relativeURL="sessionModifAC.py/remCoordinators"


class UHSessionModCoordinatorsSel(URLHandler):
    _relativeURL="sessionModifAC.py/selectCoordinators"


class UHSessionModCoordinatorsAdd(URLHandler):
    _relativeURL="sessionModifAC.py/addCoordinators"


class UHConfMyStuff(URLHandler):
    _relativeURL="myconference.py"


class UHConfModSlotRem(URLHandler):
    _relativeURL="confModifSchedule.py/remSlot"

class UHConfModSessionMove(URLHandler):
    _relativeURL="confModifSchedule.py/moveSession"

class UHConfModSessionMoveConfirmation(URLHandler):
    _relativeURL="confModifSchedule.py/moveSession"


class UHConfModSessionRem(URLHandler):
    _relativeURL="confModifSchedule.py/remSession"


class UHConfModMoveContribsToSession( URLHandler ):
    _relativeURL = "confModifContribList.py/moveToSession"

class UHConferenceDisplayMaterialPackage( URLHandler ):
    _relativeURL = "conferenceDisplay.py/matPkg"

class UHConferenceDisplayMaterialPackagePerform( URLHandler ):
    _relativeURL = "conferenceDisplay.py/performMatPkg"

class UHConferenceDisplayMenuClose( URLHandler ):
    _relativeURL = "conferenceDisplay.py/closeMenu"

class UHConferenceDisplayMenuOpen( URLHandler ):
    _relativeURL = "conferenceDisplay.py/openMenu"

class UHConferenceDisplayWriteMinutes( URLHandler ):
    _relativeURL = "conferenceDisplay.py/writeMinutes"

class UHSessionDisplayRemoveMaterial( URLHandler ):
    _relativeURL = "sessionDisplay.py/removeMaterial"

class UHConfAbstractBook( URLHandler ):
    _relativeURL = "conferenceDisplay.py/abstractBook"

class UHConfAbstractBookLatex( URLHandler ):
    _relativeURL = "conferenceDisplay.py/abstractBookLatex"

class UHConfAbstractBookPerform( URLHandler ):
    _relativeURL = "conferenceDisplay.py/abstractBookPerform"

class UHConferenceToiCal( URLHandler ):
    _relativeURL = "conferenceDisplay.py/ical"

class UHConfModAbstractBook( URLHandler ):
    _relativeURL = "confModBOA.py"

class UHConfModAbstractBookEdit( URLHandler ):
    _relativeURL = "confModBOA.py/edit"

class UHConfModScheduleDataEdit( URLHandler ):
    _relativeURL = "confModifSchedule.py/edit"

class UHConfModMaterialPackage( URLHandler ):
    _relativeURL = "confModifContribList.py/matPkg"

class UHConfModProceedings( URLHandler ):
    _relativeURL = "confModifContribList.py/proceedings"

class UHConfModFullMaterialPackage( URLHandler ):
    _relativeURL = "confModifTools.py/matPkg"

class UHConfModFullMaterialPackagePerform( URLHandler ):
    _relativeURL = "confModifTools.py/performMatPkg"

class UHTaskManager( URLHandler ):
    _relativeURL = "taskManager.py"

class UHRemoveTask( URLHandler ):
    _relativeURL = "taskManager.py/removeTask"

class UHUpdateNews( URLHandler ):
    _relativeURL = "updateNews.py"

# Server Admin, plugin management related
class UHAdminPlugins( URLHandler ):
    _relativeURL = "adminPlugins.py"

class UHAdminPluginsSaveOptionReloadAll( URLHandler ):
    _relativeURL = "adminPlugins.py/saveOptionReloadAll"

class UHAdminPluginsReloadAll( URLHandler ):
    _relativeURL = "adminPlugins.py/reloadAll"

class UHAdminPluginsClearAllInfo( URLHandler ):
    _relativeURL = "adminPlugins.py/clearAllInfo"

class UHAdminReloadPlugins( URLHandler ):
    _relativeURL = "adminPlugins.py/reload"

class UHAdminTogglePluginType( URLHandler ):
    _relativeURL = "adminPlugins.py/toggleActivePluginType"

class UHAdminTogglePlugin( URLHandler ):
    _relativeURL = "adminPlugins.py/toggleActive"

class UHAdminPluginsTypeSaveOptions ( URLHandler ):
    _relativeURL = "adminPlugins.py/savePluginTypeOptions"

class UHAdminPluginsSaveOptions ( URLHandler ):
    _relativeURL = "adminPlugins.py/savePluginOptions"
# End of Server Admin, plugin management related


class UHMaintenance( URLHandler ):
    _relativeURL = "adminMaintenance.py"

class UHMaintenanceTmpCleanup( URLHandler ):
    _relativeURL = "adminMaintenance.py/tmpCleanup"

class UHMaintenancePerformTmpCleanup( URLHandler ):
    _relativeURL = "adminMaintenance.py/performTmpCleanup"

class UHMaintenancePack( URLHandler ):
    _relativeURL = "adminMaintenance.py/pack"

class UHMaintenancePerformPack( URLHandler ):
    _relativeURL = "adminMaintenance.py/performPack"

class UHMaintenanceWebsessionCleanup( URLHandler ):
    _relativeURL = "adminMaintenance.py/websessionCleanup"

class UHMaintenancePerformWebsessionCleanup( URLHandler ):
    _relativeURL = "adminMaintenance.py/performWebsessionCleanup"

class UHTemplates( URLHandler ):
    _relativeURL = "adminTemplates.py"

class UHTemplatesSetDefaultPDFOptions( URLHandler ):
    _relativeURL = "adminTemplates.py/setDefaultPDFOptions"

class UHServices( URLHandler ):
    _relativeURL = "adminServices.py"

class UHRecording( URLHandler ):
    _relativeURL = "adminServices.py/recording"

class UHWebcast( URLHandler ):
    _relativeURL = "adminServices.py/webcast"

class UHWebcastICal( URLHandler ):
    _relativeURL = "adminServices.py/webcastICal"

class UHWebcastArchive( URLHandler ):
    _relativeURL = "adminServices.py/webcastArchive"

class UHWebcastSetup( URLHandler ):
    _relativeURL = "adminServices.py/webcastSetup"

class UHWebcastSelectManager( URLHandler ):
    _relativeURL = "adminServices.py/webcastSelectManager"

class UHWebcastAddManager( URLHandler ):
    _relativeURL = "adminServices.py/webcastAddManager"

class UHWebcastRemoveManager( URLHandler ):
    _relativeURL = "adminServices.py/webcastRemoveManager"

class UHWebcastAddWebcast( URLHandler ):
    _relativeURL = "adminServices.py/webcastAddWebcast"

class UHWebcastRemoveWebcast( URLHandler ):
    _relativeURL = "adminServices.py/webcastRemoveWebcast"

class UHWebcastArchiveWebcast( URLHandler ):
    _relativeURL = "adminServices.py/webcastArchiveWebcast"

class UHWebcastUnArchiveWebcast( URLHandler ):
    _relativeURL = "adminServices.py/webcastUnArchiveWebcast"

class UHWebcastModifyChannel( URLHandler ):
    _relativeURL = "adminServices.py/webcastModifyChannel"

class UHWebcastAddChannel( URLHandler ):
    _relativeURL = "adminServices.py/webcastAddChannel"

class UHWebcastRemoveChannel( URLHandler ):
    _relativeURL = "adminServices.py/webcastRemoveChannel"

class UHWebcastSwitchChannel( URLHandler ):
    _relativeURL = "adminServices.py/webcastSwitchChannel"

class UHWebcastMoveChannelUp( URLHandler ):
    _relativeURL = "adminServices.py/webcastMoveChannelUp"

class UHWebcastMoveChannelDown( URLHandler ):
    _relativeURL = "adminServices.py/webcastMoveChannelDown"

class UHWebcastSaveWebcastServiceURL( URLHandler ):
    _relativeURL = "adminServices.py/webcastSaveWebcastServiceURL"

class UHWebcastSaveWebcastSynchronizationURL( URLHandler ):
    _relativeURL = "adminServices.py/webcastSaveWebcastSynchronizationURL"

class UHWebcastManualSynchronization( URLHandler ):
    _relativeURL = "adminServices.py/webcastManualSynchronization"

class UHWebcastAddStream( URLHandler ):
    _relativeURL = "adminServices.py/webcastAddStream"

class UHWebcastRemoveStream( URLHandler ):
    _relativeURL = "adminServices.py/webcastRemoveStream"

class UHWebcastAddOnAir( URLHandler ):
    _relativeURL = "adminServices.py/webcastAddOnAir"

class UHWebcastRemoveFromAir( URLHandler ):
    _relativeURL = "adminServices.py/webcastRemoveFromAir"

class UHOAIPrivateConfig( URLHandler ):
    _relativeURL = "adminServices.py/oaiPrivateConfig"

class UHOAIPrivateConfigAddIP( URLHandler ):
    _relativeURL = "adminServices.py/oaiPrivateConfigAddIP"

class UHOAIPrivateConfigRemoveIP( URLHandler ):
    _relativeURL = "adminServices.py/oaiPrivateConfigRemoveIP"

class UHBadgeTemplates( URLHandler ):
    _relativeURL = "badgeTemplates.py"

class UHPosterTemplates( URLHandler ):
    _relativeURL = "posterTemplates.py"

class UHAnnouncement( URLHandler ):
    _relativeURL = "adminAnnouncement.py"

class UHAnnouncementSave( URLHandler ):
    _relativeURL = "adminAnnouncement.py/save"

class UHConfigUpcomingEvents( URLHandler ):
    _relativeURL = "adminUpcomingEvents.py"

class UHMaterialMainResourceSelect( URLHandler ):
    _relativeURL = "materialModification.py/selectMainResource"

class UHMaterialMainResourcePerformSelect( URLHandler ):
    _relativeURL = "materialModification.py/performSelectMainResource"

# ------- DVD creation and static webpages ------

class UHConfDVDCreation( URLHandler ):
    _relativeURL = "confModifTools.py/dvdCreation"

class UHStaticConferenceDisplay( URLHandler ):
    _relativeURL = "./index.html"

class UHStaticMaterialDisplay( URLHandler ):
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

class UHStaticConfAbstractBook( URLHandler ):
    _relativeURL = "./abstractBook.pdf"

class UHStaticConferenceProgram( URLHandler ):
    _relativeURL = "./programme.html"

class UHStaticConferenceTimeTable( URLHandler ):
    _relativeURL = "./timetable.html"

class UHStaticContributionList( URLHandler ):
    _relativeURL = "./contributionList.html"

class UHStaticConfAuthorIndex( URLHandler ):
    _relativeURL = "./authorIndex.html"

class UHStaticContributionDisplay( URLHandler ):
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

class UHStaticSessionDisplay( URLHandler ):
    _relativeURL = ""

    def getRelativeURL(cls, target=None):
        return "./sessions/s%s.html"%target.getId()
    getRelativeURL = classmethod( getRelativeURL )

class UHStaticResourceDisplay( URLHandler ):
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

class UHStaticTrackContribList( URLHandler ):
    _relativeURL = ""

    def getRelativeURL(cls, target=None, escape=True):
        url = cls._relativeURL
        if target is not None:
            url = "%s.html"%(target.getTitle().replace(" ","_"))

        if escape:
            url = utf8rep(url)
        return url

    getRelativeURL = classmethod( getRelativeURL )

class UHDVDDone( URLHandler ):
    _relativeURL = "confModifTools.py/dvdDone"


class UHMStaticMaterialDisplay( URLHandler ):
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

class UHMStaticResourceDisplay( URLHandler ):
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

class UHContribAuthorDisplay( URLHandler ):
    _relativeURL = "contribAuthorDisplay.py"

class UHConfTimeTableCustomizePDF( URLHandler ):
    _relativeURL = "conferenceTimeTable.py/customizePdf"

class UHConfRegistrationForm( URLHandler ):
    _relativeURL = "confRegistrationFormDisplay.py"

class UHConfRegistrationFormDisplay( URLHandler ):
    _relativeURL = "confRegistrationFormDisplay.py/display"

class UHConfRegistrationFormCreation( URLHandler ):
    _relativeURL = "confRegistrationFormDisplay.py/creation"

class UHConfRegistrationFormConditions( URLHandler ):
    _relativeURL = "confRegistrationFormDisplay.py/conditions"

class UHConfRegistrationFormSignIn( URLHandler ):
    _relativeURL = "confRegistrationFormDisplay.py/signIn"

    def getURL( cls, conf, returnURL="" ):
        url = cls._getURL()
        url.setParams(conf.getLocator())
        if str(returnURL).strip() != "":
            url.addParam( "returnURL", returnURL )
        return url
    getURL = classmethod( getURL )

class UHConfRegistrationFormCreationDone( URLHandler ):
    _relativeURL = "confRegistrationFormDisplay.py/creationDone"

    def getURL( cls, registrant):
        url = cls._getURL()
        url.setParams(registrant.getLocator())
        url.addParam( "authkey", registrant.getRandomId() )
        return url
    getURL = classmethod( getURL )

class UHConfRegistrationFormconfirmBooking( URLHandler ):
    _relativeURL = "confRegistrationFormDisplay.py/confirmBooking"

class UHConfRegistrationFormconfirmBookingDone( URLHandler ):
    _relativeURL = "confRegistrationFormDisplay.py/confirmBookingDone"

class UHConfRegistrationFormModify( URLHandler ):
    _relativeURL = "confRegistrationFormDisplay.py/modify"

class UHConfRegistrationFormPerformModify( URLHandler ):
    _relativeURL = "confRegistrationFormDisplay.py/performModify"

###################################################################################
## epayment url
class UHConfModifEPayment( URLHandler ):
    _relativeURL = "confModifEpayment.py"

class UHConfModifEPaymentEnableSection( URLHandler ):
    _relativeURL = "confModifEpayment.py/enableSection"
class UHConfModifEPaymentChangeStatus( URLHandler ):
    _relativeURL = "confModifEpayment.py/changeStatus"
#class UHConfModifEPaymentDataModification( URLHandler ):
class UHConfModifEPaymentdetailPaymentModification( URLHandler ):
    _relativeURL = "confModifEpayment.py/dataModif"
class UHConfModifEPaymentPerformdetailPaymentModification( URLHandler ):
    _relativeURL = "confModifEpayment.py/performDataModif"

###################################################################################


class UHConfModifRegForm( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py"

class UHConfModifRegFormChangeStatus( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/changeStatus"

class UHConfModifRegFormDataModification( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/dataModif"

class UHConfModifRegFormPerformDataModification( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/performDataModif"

class UHConfModifRegFormSessions( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/modifSessions"

class UHConfModifRegFormSessionsDataModif( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/modifSessionsData"

class UHConfModifRegFormSessionsPerformDataModif( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/performModifSessionsData"

class UHConfModifRegFormSessionsAdd( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/addSession"

class UHConfModifRegFormSessionsPerformAdd( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/performAddSession"

class UHConfModifRegFormSessionsRemove( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/removeSession"

class UHConfModifRegFormAccommodation( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/modifAccommodation"

class UHConfModifRegFormAccommodationDataModif( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/modifAccommodationData"

class UHConfModifRegFormAccommodationPerformDataModif( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/performModifAccommodationData"

class UHConfModifRegFormAccommodationTypeRemove( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/removeAccommodationType"

class UHConfModifRegFormAccommodationTypeAdd( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/addAccommodationType"

class UHConfModifRegFormAccommodationTypePerformAdd( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/performAddAccommodationType"

class UHConfModifRegFormAccommodationTypeModify( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/modifyAccommodationType"

class UHConfModifRegFormAccommodationTypePerformModify( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/performModifyAccommodationType"

class UHConfModifRegFormReasonParticipation( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/modifReasonParticipation"

class UHConfModifRegFormReasonParticipationDataModif( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/modifReasonParticipationData"

class UHConfModifRegFormReasonParticipationPerformDataModif( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/performModifReasonParticipationData"

class UHConfModifRegFormFurtherInformation( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/modifFurtherInformation"

class UHConfModifRegFormFurtherInformationDataModif( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/modifFurtherInformationData"

class UHConfModifRegFormFurtherInformationPerformDataModif( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/performModifFurtherInformationData"

class UHConfModifRegFormSocialEvent( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/modifSocialEvent"

class UHConfModifRegFormSocialEventDataModif( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/modifSocialEventData"

class UHConfModifRegFormSocialEventPerformDataModif( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/performModifSocialEventData"

class UHConfModifRegFormSocialEventRemove( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/removeSocialEvent"

class UHConfModifRegFormSocialEventAdd( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/addSocialEvent"

class UHConfModifRegFormSocialEventPerformAdd( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/performAddSocialEvent"

class UHConfModifRegFormSocialEventItemModify( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/modifySocialEventItem"

class UHConfModifRegFormSocialEventItemPerformModify( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/performModifySocialEventItem"

class UHConfModifRegFormActionStatuses( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/actionStatuses"

class UHConfModifRegFormStatusModif( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/modifStatus"

class UHConfModifRegFormStatusPerformModif( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/performModifStatus"

class UHConfModifRegFormActionSection( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/actionSection"

class UHConfModifRegFormGeneralSection( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/modifGeneralSection"

class UHConfModifRegFormGeneralSectionDataModif( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/modifGeneralSectionData"

class UHConfModifRegFormGeneralSectionPerformDataModif( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/performModifGeneralSectionData"

class UHConfModifRegFormGeneralSectionFieldAdd( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/addGeneralField"

class UHConfModifRegFormGeneralSectionFieldPerformAdd( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/performAddGeneralField"

class UHConfModifRegFormGeneralSectionFieldRemove( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/removeGeneralField"

class UHConfModifRegFormGeneralSectionFieldModif( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/modifGeneralField"

class UHConfModifRegFormGeneralSectionFieldPerformModif( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/performModifGeneralField"

class UHConfModifRegistrationPreview( URLHandler ):
    _relativeURL = "confModifRegistrationPreview.py"

class UHConfModifRegistrantList( URLHandler ):
    _relativeURL = "confModifRegistrants.py"

class UHConfModifRegistrantsOpenMenu( URLHandler ):
    _relativeURL = "confModifRegistrants.py/openMenu"

class UHConfModifRegistrantsCloseMenu( URLHandler ):
    _relativeURL = "confModifRegistrants.py/closeMenu"

class UHConfModifRegistrantListAction( URLHandler ):
    _relativeURL = "confModifRegistrants.py/action"

class UHConfModifRegistrantPerformRemove( URLHandler ):
    _relativeURL = "confModifRegistrants.py/remove"

class UHRegistrantModification( URLHandler ):
    _relativeURL = "confModifRegistrants.py/modification"

class UHRegistrantDataModification( URLHandler ):
    _relativeURL = "confModifRegistrants.py/dataModification"

class UHRegistrantPerformDataModification( URLHandler ):
    _relativeURL = "confModifRegistrants.py/performDataModification"

class UHConfModifRegFormEnableSection( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/enableSection"

class UHConfModifRegFormEnablePersonalField( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/enablePersonalField"

class UHConfModifRegFormSwitchPersonalField( URLHandler ):
    _relativeURL = "confModifRegistrationForm.py/switchPersonalField"

class UHCategoryStatistics( URLHandler ):
    _relativeURL = "categoryStatistics.py"

class UHCategoryToiCal( URLHandler ):
    _relativeURL = "categoryDisplay.py/ical"

class UHCategoryToRSS( URLHandler ):
    _relativeURL = "categoryDisplay.py/rss"

class UHCategOverviewToRSS( URLHandler ):
    _relativeURL = "categOverview.py/rss"

class UHConfRegistrantsList( URLHandler ):
    _relativeURL = "confRegistrantsDisplay.py/list"

class UHConfModifRegistrantSessionModify( URLHandler ):
    _relativeURL = "confModifRegistrants.py/modifySessions"

class UHConfModifRegistrantSessionPeformModify( URLHandler ):
    _relativeURL = "confModifRegistrants.py/performModifySessions"

class UHConfModifRegistrantTransactionModify( URLHandler ):
    _relativeURL = "confModifRegistrants.py/modifyTransaction"

class UHConfModifRegistrantTransactionPeformModify( URLHandler ):
    _relativeURL = "confModifRegistrants.py/peformModifyTransaction"

class UHConfModifRegistrantAccoModify( URLHandler ):
    _relativeURL = "confModifRegistrants.py/modifyAccommodation"

class UHConfModifRegistrantAccoPeformModify( URLHandler ):
    _relativeURL = "confModifRegistrants.py/performModifyAccommodation"

class UHConfModifRegistrantSocialEventsModify( URLHandler ):
    _relativeURL = "confModifRegistrants.py/modifySocialEvents"

class UHConfModifRegistrantSocialEventsPeformModify( URLHandler ):
    _relativeURL = "confModifRegistrants.py/performModifySocialEvents"

class UHConfModifRegistrantReasonPartModify( URLHandler ):
    _relativeURL = "confModifRegistrants.py/modifyReasonParticipation"

class UHConfModifRegistrantReasonPartPeformModify( URLHandler ):
    _relativeURL = "confModifRegistrants.py/performModifyReasonParticipation"

class UHConfModifPendingQueues( URLHandler ):
    _relativeURL = "confModifPendingQueues.py"

class UHConfModifPendingQueuesActionSubm( URLHandler ):
    _relativeURL = "confModifPendingQueues.py/actionSubmitters"

class UHConfModifPendingQueuesActionMgr( URLHandler ):
    _relativeURL = "confModifPendingQueues.py/actionManagers"

class UHConfModifPendingQueuesActionCoord( URLHandler ):
    _relativeURL = "confModifPendingQueues.py/actionCoordinators"

class UHConfModifRegistrantMiscInfoModify( URLHandler ):
    _relativeURL = "confModifRegistrants.py/modifyMiscInfo"

class UHConfModifRegistrantMiscInfoPerformModify( URLHandler ):
    _relativeURL = "confModifRegistrants.py/performModifyMiscInfo"

class UHUserSearchCreateExternalUser( URLHandler ):
    _relativeURL = "userSelection.py/createExternalUsers"

class UHConfModifRegistrantStatusesModify( URLHandler ):
    _relativeURL = "confModifRegistrants.py/modifyStatuses"

class UHConfModifRegistrantStatusesPerformModify( URLHandler ):
    _relativeURL = "confModifRegistrants.py/performModifyStatuses"

class UHGetCalendarOverview( URLHandler ):
    _relativeURL ="categOverview.py"

class UHCategoryCalendarOverview( URLHandler ):
    _relativeURL ="wcalendar.py"


"""
URL Handlers for  Printing and Design
"""
class UHConfModifBadgePrinting ( URLHandler ):
    _relativeURL = "confModifTools.py/badgePrinting"

    def getURL( cls, target=None, templateId=None, deleteTemplateId=None, cancel=False, new=False, copyTemplateId=None ):
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
    getURL = classmethod( getURL )

class UHConfModifBadgeDesign ( URLHandler ):
    _relativeURL = "confModifTools.py/badgeDesign"

    def getURL( cls, target=None, templateId=None, new=False):
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
    getURL = classmethod( getURL )

class UHModifDefTemplateBadge ( URLHandler ):
    _relativeURL = "badgeTemplates.py/badgeDesign"

    def getURL( cls, target=None, templateId=None, new=False):
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
    getURL = classmethod( getURL )

class UHConfModifBadgeSaveBackground ( URLHandler ):
    _relativeURL = "confModifTools.py/badgeSaveBackground"

    def getURL( cls, target=None, templateId=None ):
        url = cls._getURL()
        if target is not None and templateId is not None:
            url.setParams(target.getLocator())
            url.addParam("templateId", templateId)
        return url
    getURL = classmethod( getURL )

class UHConfModifBadgeGetBackground ( URLHandler ):
    _relativeURL = "confModifTools.py/badgeGetBackground"

    def getURL( cls, target=None, templateId=None, backgroundId=None):
        url = cls._getURL()
        if target is not None and templateId is not None:
            url.setParams(target.getLocator())
            url.addParam("templateId", templateId)
            url.addParam("backgroundId", backgroundId)
        return url
    getURL = classmethod( getURL )

class UHConfModifBadgePrintingPDF ( URLHandler ):
    _relativeURL = "confModifTools.py/badgePrintingPDF"

"""
URL Handlers for Poster Printing and Design
"""
class UHConfModifPosterPrinting ( URLHandler ):
    _relativeURL = "confModifTools.py/posterPrinting"

    def getURL( cls, target=None, templateId=None, deleteTemplateId=None, cancel=False, new=False, copyTemplateId=None ):
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
    getURL = classmethod( getURL )

class UHConfModifPosterDesign ( URLHandler ):
    _relativeURL = "confModifTools.py/posterDesign"

    def getURL( cls, target=None, templateId=None, new=False):
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
    getURL = classmethod( getURL )

class UHModifDefTemplatePoster ( URLHandler ):
    _relativeURL = "posterTemplates.py/posterDesign"

    def getURL( cls, target=None, templateId=None, new=False):
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
    getURL = classmethod( getURL )

class UHConfModifPosterSaveBackground ( URLHandler ):
    _relativeURL = "confModifTools.py/posterSaveBackground"

    def getURL( cls, target=None, templateId=None ):
        url = cls._getURL()
        if target is not None and templateId is not None:
            url.setParams(target.getLocator())
            url.addParam("templateId", templateId)
        return url
    getURL = classmethod( getURL )

class UHConfModifPosterGetBackground ( URLHandler ):
    _relativeURL = "confModifTools.py/posterGetBackground"

    def getURL( cls, target=None, templateId=None, backgroundId=None):
        url = cls._getURL()
        if target is not None and templateId is not None:
            url.setParams(target.getLocator())
            url.addParam("templateId", templateId)
            url.addParam("backgroundId", backgroundId)
        return url
    getURL = classmethod( getURL )

class UHConfModifPosterPrintingPDF ( URLHandler ):
    _relativeURL = "confModifTools.py/posterPrintingPDF"


"""
URL Handlers for Javascript Packages
"""
class UHJsonRpcService (URLHandler):
    _relativeURL = "services/json-rpc"

class UHSecureJsonRpcService (SecureURLHandler):
    _relativeURL = "services/json-rpc"

class UHJavascriptCalendar (URLHandler):
    _relativeURL = "js/calendar/calendar.js"

class UHJavascriptCalendarSetup (URLHandler):
    _relativeURL = "js/calendar/calendar-setup.js"

############
#Evaluation# DISPLAY AREA
############

class UHConfEvaluationMainInformation( URLHandler ):
    _relativeURL = "confDisplayEvaluation.py"

class UHConfEvaluationDisplay( URLHandler ):
    _relativeURL = "confDisplayEvaluation.py/display"

class UHConfEvaluationDisplayModif( URLHandler ):
    _relativeURL = "confDisplayEvaluation.py/modif"

class UHConfEvaluationSignIn( URLHandler ):
    _relativeURL = "confDisplayEvaluation.py/signIn"

    def getURL( cls, conf, returnURL="" ):
        url = cls._getURL()
        url.setParams(conf.getLocator())
        if str(returnURL).strip() != "":
            url.addParam( "returnURL", returnURL )
        return url
    getURL = classmethod( getURL )

class UHConfEvaluationSubmit( URLHandler ):
    _relativeURL = "confDisplayEvaluation.py/submit"

class UHConfEvaluationSubmitted( URLHandler ):
    _relativeURL = "confDisplayEvaluation.py/submitted"

############
#Evaluation# MANAGEMENT AREA
############
class UHConfModifEvaluation( URLHandler ):
    _relativeURL = "confModifEvaluation.py"

class UHConfModifEvaluationSetup( URLHandler ):
    """same result as UHConfModifEvaluation."""
    _relativeURL = "confModifEvaluation.py/setup"

class UHConfModifEvaluationSetupChangeStatus( URLHandler ):
    _relativeURL = "confModifEvaluation.py/changeStatus"

class UHConfModifEvaluationSetupSpecialAction( URLHandler ):
    _relativeURL = "confModifEvaluation.py/specialAction"

class UHConfModifEvaluationDataModif( URLHandler ):
    _relativeURL = "confModifEvaluation.py/dataModif"

class UHConfModifEvaluationPerformDataModif( URLHandler ):
    _relativeURL = "confModifEvaluation.py/performDataModif"

class UHConfModifEvaluationEdit( URLHandler ):
    _relativeURL = "confModifEvaluation.py/edit"

class UHConfModifEvaluationEditPerformChanges( URLHandler ):
    _relativeURL = "confModifEvaluation.py/editPerformChanges"

class UHConfModifEvaluationPreview( URLHandler ):
    _relativeURL = "confModifEvaluation.py/preview"

class UHConfModifEvaluationResults( URLHandler ):
    _relativeURL = "confModifEvaluation.py/results"

class UHConfModifEvaluationResultsOptions( URLHandler ):
    _relativeURL = "confModifEvaluation.py/resultsOptions"

class UHConfModifEvaluationResultsSubmittersActions( URLHandler ):
    _relativeURL = "confModifEvaluation.py/resultsSubmittersActions"

############
# Personalization
############

# "My Events"

class UHGetUserEventPage( URLHandler ):
    _relativeURL = "userDetails.py/getEvents"

    @classmethod
    def getURL( cls, target=None ):
        url = cls._getURL()

        if (target != None):
            url.setParams( target.getLocator() )

        return url

class UHResetSession (URLHandler):
    _relativeURL = "resetSessionTZ.py"

##############
# Reviewing
#############
class UHConfModifReviewingAccess ( URLHandler ):
    _relativeURL = "confModifReviewing.py/access"

class UHConfModifReviewingPaperSetup( URLHandler ):
    _relativeURL = "confModifReviewing.py/paperSetup"

class UHChooseReviewing( URLHandler ):
    _relativeURL = "confModifReviewing.py/chooseReviewing"

class UHAddState( URLHandler ):
    _relativeURL = "confModifReviewing.py/addState"

class UHRemoveState( URLHandler ):
    _relativeURL = "confModifReviewing.py/removeState"

class UHAddQuestion( URLHandler ):
    _relativeURL = "confModifReviewing.py/addQuestion"

class UHRemoveQuestion( URLHandler ):
    _relativeURL = "confModifReviewing.py/removeQuestion"

class UHSetTemplate( URLHandler ):
    _relativeURL = "confModifReviewing.py/setTemplate"

class UHAddCriteria( URLHandler ):
    _relativeURL = "confModifReviewing.py/addCriteria"

class UHRemoveCriteria( URLHandler ):
    _relativeURL = "confModifReviewing.py/removeCriteria"

class UHDownloadContributionTemplate( URLHandler ):
    _relativeURL = "confModifReviewing.py/downloadTemplate"

class UHDeleteContributionTemplate( URLHandler ):
    _relativeURL = "confModifReviewing.py/deleteTemplate"

class UHConfModifReviewingAbstractSetup ( URLHandler ):
    _relativeURL = "confModifReviewing.py/abstractSetup"

class UHConfModifReviewingControl ( URLHandler ):
    _relativeURL = "confModifReviewingControl.py"

class UHConfModifUserCompetences ( URLHandler ):
    _relativeURL = "confModifUserCompetences.py"

class UHConfModifModifyUserCompetences ( URLHandler ):
    _relativeURL = "confModifUserCompetences.py/modifyCompetences"

class UHConfSelectPaperReviewManager( URLHandler ):
    _relativeURL = "confModifReviewingControl.py/selectPaperReviewManager"

class UHConfAddPaperReviewManager( URLHandler ):
    _relativeURL = "confModifReviewingControl.py/addPaperReviewManager"

class UHConfRemovePaperReviewManager( URLHandler ):
    _relativeURL = "confModifReviewingControl.py/removePaperReviewManager"

class UHConfSelectAbstractManager( URLHandler ):
    _relativeURL = "confModifReviewingControl.py/selectAbstractManager"

class UHConfAddAbstractManager( URLHandler ):
    _relativeURL = "confModifReviewingControl.py/addAbstractManager"

class UHConfRemoveAbstractManager( URLHandler ):
    _relativeURL = "confModifReviewingControl.py/removeAbstractManager"

class UHConfSelectEditor( URLHandler ):
    _relativeURL = "confModifReviewingControl.py/selectEditor"

class UHConfAddEditor( URLHandler ):
    _relativeURL = "confModifReviewingControl.py/addEditor"

class UHConfRemoveEditor( URLHandler ):
    _relativeURL = "confModifReviewingControl.py/removeEditor"

class UHConfSelectReviewer( URLHandler ):
    _relativeURL = "confModifReviewingControl.py/selectReviewer"

class UHConfAddReviewer( URLHandler ):
    _relativeURL = "confModifReviewingControl.py/addReviewer"

class UHConfRemoveReviewer( URLHandler ):
    _relativeURL = "confModifReviewingControl.py/removeReviewer"

class UHConfSelectAbstractReviewer( URLHandler ):
    _relativeURL = "confModifReviewingControl.py/selectAbstractReviewer"

class UHConfAddAbstractReviewer( URLHandler ):
    _relativeURL = "confModifReviewingControl.py/addAbstractReviewer"

class UHConfRemoveAbstractReviewer( URLHandler ):
    _relativeURL = "confModifReviewingControl.py/removeAbstractReviewer"

class UHConfSelectReferee( URLHandler ):
    _relativeURL = "confModifReviewingControl.py/selectReferee"

class UHConfAddReferee( URLHandler ):
    _relativeURL = "confModifReviewingControl.py/addReferee"

class UHConfRemoveReferee( URLHandler ):
    _relativeURL = "confModifReviewingControl.py/removeReferee"

class UHConfModifListContribToJudge( URLHandler ):
    _relativeURL = "confListContribToJudge.py"

class UHConfModifReviewingAssignContributionsList( URLHandler ):
    _relativeURL = "assignContributions.py"

class UHConfModifReviewingAssignContributionsAssign( URLHandler ):
    _relativeURL = "assignContributions.py/assign"


#Contribution reviewing
class UHContributionModifReviewing( URLHandler ):
    _relativeURL = "contributionReviewing.py"

class UHContributionSubmitForRewiewing( URLHandler ):
    _relativeURL = "contributionReviewing.py/submitForReviewing"

class UHContributionRemoveSubmittedMarkForReviewing( URLHandler ):
    _relativeURL = "contributionReviewing.py/removeSubmittedMarkForReviewing"

class UHAssignReferee(URLHandler):
    _relativeURL = "contributionReviewing.py/assignReferee"

class UHRemoveAssignReferee(URLHandler):
    _relativeURL = "contributionReviewing.py/removeAssignReferee"

class UHAssignEditing( URLHandler ):
    _relativeURL = "contributionReviewing.py/assignEditing"

class UHRemoveAssignEditing( URLHandler ):
    _relativeURL = "contributionReviewing.py/removeAssignEditing"

class UHAssignReviewing( URLHandler ):
    _relativeURL = "contributionReviewing.py/assignReviewing"

class UHRemoveAssignReviewing( URLHandler ):
    _relativeURL = "contributionReviewing.py/removeAssignReviewing"

class UHFinalJudge( URLHandler ):
    _relativeURL = "contributionReviewing.py/finalJudge"

class UHContributionModifReviewingHistory( URLHandler ):
    _relativeURL = "contributionReviewing.py/reviewingHistory"

class UHContributionEditingJudgement( URLHandler ):
    _relativeURL = "contributionEditingJudgement.py"

class UHJudgeEditing( URLHandler ):
    _relativeURL = "contributionEditingJudgement.py/judgeEditing"

class UHContributionGiveAdvice( URLHandler ):
    _relativeURL = "contributionGiveAdvice.py"

class UHGiveAdvice( URLHandler ):
    _relativeURL = "contributionGiveAdvice.py/giveAdvice"

class UHRefereeDueDate (URLHandler):
    _relativeURL = "contributionReviewing.py/refereeDueDate"

class UHEditorDueDate (URLHandler):
    _relativeURL = "contributionReviewing.py/editorDueDate"

class UHReviewerDueDate (URLHandler):
    _relativeURL = "contributionReviewing.py/reviewerDueDate"

#### End of reviewing

class UHChangeLang( URLHandler ):
    _relativeURL = "changeLang.py"

class UHAbout( URLHandler ):
    _relativeURL = "about.py"

class UHContact( URLHandler ):
    _relativeURL = "contact.py"

class UHHelper(object):
    """ Returns the display or modif UH for an object of a given class
    """

    modifUHs = {
        "Category" : UHCategoryModification,
        "Conference" : UHConferenceModification,
        "DefaultConference" : UHConferenceModification,
        "Contribution": UHContributionModification,
        "AcceptedContribution": UHContributionModification,
        "Session" : UHSessionModification,
        "SubContribution" : UHSubContributionModification,
        "Abstract": UHAbstractModification,
        "Track" : UHTrackModification,
        "SubTrack" : UHTrackModifSubTrack
    }

    displayUHs = {
        "Category" : UHCategoryDisplay,
        "CategoryMap" : UHCategoryMap,
        "CategoryOverview" : UHCategoryOverview,
        "CategoryStatistics" : UHCategoryStatistics,
        "CategoryCalendar" : UHCategoryCalendarOverview,
        "Conference" : UHConferenceDisplay,
        "Contribution": UHContributionDisplay,
        "AcceptedContribution": UHContributionDisplay,
        "Session" : UHSessionDisplay,
        "Abstract": UHAbstractDisplay
    }

    @classmethod
    def getModifUH(cls, klazz):
        return cls.modifUHs.get(klazz.__name__, None)

    @classmethod
    def getDisplayUH(cls, klazz, type=""):
        return cls.displayUHs.get("%s%s"%(klazz.__name__, type), None)

# Testing helloworld
class UHHelloWorld(URLHandler):
    _relativeURL = "helloWorld.py"

    @classmethod
    def getURL( cls, name=None ):
        url = cls._getURL()
        if name != None:
            url.addParam("name", name)
        return url
