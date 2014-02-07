# -*- coding: utf-8 -*-
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

""" This file has the common fossils for Collaboration
    There are 3 groups of fossils:
        -base fossils for the plugin's CSBooking classes,
        -base fossils for the plugin's CSError classes,
        -fossils used by the core for the Video Services Overview page (they are not base fossils for plugins)

"""


from MaKaC.common.fossilize import IFossil
from MaKaC.fossils.conference import IConferenceFossil, IConferenceMinimalFossil
from MaKaC.fossils.contribution import IContributionFossil
from MaKaC.common.Conversion import Conversion
from MaKaC.plugins import Collaboration


class ISpeakerWrapperBaseFossil(IFossil):

    def getUniqueId(self):
        pass

    def getStatus(self):
        pass

    def getContId(self):
        pass

    def getSpeakerId(self):
        pass

##################### Booking fossils #####################
class ICSBookingBaseFossil(IFossil):

    def getId(self):
        """ Returns the internal, per-conference id of the booking. """

    def getType(self):
        """ Returns the type of the booking, as a string: EVO, CERNMCU, etc. """

    def getAdjustedCreationDate(self):
        """ Returns the booking creation date, adjusted to a given timezone """
    getAdjustedCreationDate.name = "creationDate"
    getAdjustedCreationDate.convert = Conversion.datetime

    def getAdjustedModificationDate(self):
        """ Returns the booking last modification date, adjusted to a given timezone """
    getAdjustedModificationDate.name = "modificationDate"
    getAdjustedModificationDate.convert = Conversion.datetime

    def getStatusMessage(self):
        """ Returns the status message as a string. """

    def getStatusClass(self):
        """ Returns the status message CSS class as a string. """

    def getAcceptRejectStatus(self):
        """ Returns the Accept/Reject status of the booking """

    def getBookingParams(self):
        """ Returns a dictionary with the booking params. """

    def hasAcceptReject(self):
        """ Returns if this booking belongs to a plugin who has a "accept or reject" concept. """


class ICSBookingBaseConfModifFossil(ICSBookingBaseFossil):

    def getConference(self):
        """ Returns the assocaited event id """
    getConference.result = IConferenceMinimalFossil

    def getWarning(self):
        """ Returns a warning object attached to this booking. (self._warning) """
    getWarning.result = None #whatever the object's default fossil is, it will be used

    def getRejectReason(self):
        """ Returns the rejection reason. """

    def hasStart(self):
        """ Returns if this booking belongs to a plugin who has a "start" concept. """

    def hasStartStopAll(self):
        """ Returns if this booking belongs to a plugin who has a "start" concept, and all of its bookings for a conference
            can be started simultanously.
        """

    def hasStop(self):
        """ Returns if this booking belongs to a plugin who has a "start" concept. """

    def hasConnect(self):
        """ Returns if this booking belongs to a plugin who has a "connect" concept. """

    def hasCheckStatus(self):
        """ Returns if this booking belongs to a plugin who has a "check status" concept. """

    def isLinkedToEquippedRoom(self):
        pass

    def requiresServerCallForStart(self):
        """ Returns if this booking belongs to a plugin who requires a server call when the start button is pressed."""
    requiresServerCallForStart.name = "requiresServerCallForStart"

    def requiresServerCallForStop(self):
        """ Returns if this booking belongs to a plugin who requires a server call when the stop button is pressed. """
    requiresServerCallForStop.name = "requiresServerCallForStop"

    def requiresClientCallForStart(self):
        """ Returns if this booking belongs to a plugin who requires a client call when the start button is pressed. """
    requiresClientCallForStart.name = "requiresClientCallForStart"

    def requiresClientCallForStop(self):
        """ Returns if this booking belongs to a plugin who requires a client call when the stop button is pressed. """
    requiresClientCallForStop.name = "requiresClientCallForStop"

    def canBeDeleted(self):
        """ Returns if this booking can be deleted, in the sense that the "Remove" button will be active and able to be pressed. """
    canBeDeleted.name = "canBeDeleted"

    def canBeStarted(self):
        """ Returns if this booking can be started, in the sense that the "Start" button will be active and able to be pressed. """
    canBeStarted.name = "canBeStarted"

    def canBeStopped(self):
        """ Returns if this booking can be stopped, in the sense that the "Stop" button will be active and able to be pressed. """
    canBeStopped.name = 'canBeStopped'

    def isPermittedToStart(self):
        """ Returns if this booking is allowed to start, in the sense that it will be started after the "Start" button is pressed.
            For example a booking should not be permitted to start before a given time, even if the button is active. """
    isPermittedToStart.name = "permissionToStart"

    def isPermittedToStop(self):
        """ Returns if this booking is allowed to stop, in the sense that it will be started after the "Stop" button is pressed."""
    isPermittedToStop.name = "permissionToStop"

    def canBeNotifiedOfEventDateChanges(self):
        """ Returns if bookings of this type should be able to be notified
            of their owner Event changing start date, end date or timezone. """
    canBeNotifiedOfEventDateChanges.name = "canBeNotifiedOfEventDateChanges"

    def isAllowMultiple(self):
        """ Returns if this booking belongs to a type that allows multiple bookings per event. """

class ICSBookingBaseIndexingFossil(ICSBookingBaseFossil):

    def getConference(self):
        """ Returns a fossil of the Conference this booking is attached to """
    getConference.result = IConferenceFossil

    def getModificationURL(self):
        pass
    getModificationURL.name = "modificationURL"
    getModificationURL.convert = lambda url: str(url)


class ICSBookingInstanceIndexingFossil(ICSBookingBaseIndexingFossil):
    def getStartDate(self):
        pass
    getStartDate.name = "instanceDate"
    getStartDate.convert = Conversion.datetime

    def getTalk(self):
        """ Returns fossil of the talk this booking relates to """
    getTalk.result = IContributionFossil


##################### Error fossils #####################

class ICSErrorBaseFossil(IFossil):

    def getError(self):
        """ Always returns True"""
    getError.produce = lambda self: True


class ICSSanitizationErrorFossil(ICSErrorBaseFossil):

    def invalidFields(self):
        pass
    invalidFields.name = "invalidFields"


##################### Indexing core fossils #####################

class IIndexInformationFossil(IFossil):

    def getName(self):
        pass

    def getPlugins(self):
        pass

    def hasShowOnlyPending(self):
        pass

    def hasViewByStartDate(self):
        pass



class IQueryResultFossil(IFossil):

    def getResults(self):
        pass
    getResults.result = None
    #the .result tag will be updated at run time because it is a dictionary whose values
    #depend on the loaded plugins, therefore, on the database state

    def getNumberOfBookings(self):
        pass
    getNumberOfBookings.name = 'nBookings'

    def getNumberOfGroups(self):
        pass
    getNumberOfGroups.name = 'nGroups'

    def getTotalInIndex(self):
        pass

    def getNPages(self):
        pass

""" MetadataFossil created for use with iCal serialisation of Collaboration /
    VideoService events.
"""
class ICollaborationMetadataFossil(IFossil):

    def getStartDateAsString(self):
        pass

    def getAcceptRejectStatus(self):
        pass
    getAcceptRejectStatus.produce = lambda s: Collaboration.collaborationTools.CollaborationTools.getBookingShortStatus(s)
    getAcceptRejectStatus.name = 'status'

    def getStartDate(self):
        pass
    getStartDate.produce = lambda s: s.getStartDate() or s.getConference().getStartDate()

    def getEndDate(self):
        pass
    getEndDate.produce = lambda s: s.getEndDate() or s.getConference().getEndDate()

    def _getTitle(self):
        pass

    _getTitle.produce = lambda s: Collaboration.collaborationTools.CollaborationTools.getBookingTitle(s.getLinkObject() if s.hasSessionOrContributionLink() else s)
    _getTitle.name = 'title'

    def getType(self):
        pass

    def getUniqueId(self):
        pass

    def getConference(self):
        pass
    getConference.name = 'event_id'
    getConference.convert = lambda e: e.getId()

    def getLocation(self):
        pass

    def getRoom(self):
        pass

    def getURL(self):
        pass
    getURL.produce = lambda s: str(Collaboration.collaborationTools.CollaborationTools.getConferenceOrContributionURL(s))
    getURL.name = 'url'

    def getAudience(self):
        pass
    getAudience.produce = lambda s: Collaboration.collaborationTools.CollaborationTools.getAudience(s)
    getAudience.name = 'audience'
