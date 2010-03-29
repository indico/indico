# -*- coding: utf-8 -*-
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

""" This file has the common fossils for Collaboration
    There are 3 groups of fossils:
        -base fossils for the plugin's CSBooking classes,
        -base fossils for the plugin's CSError classes,
        -fossils used by the core for the Video Services Overview page (they are not base fossils for plugins)

"""


from MaKaC.common.fossilize import IFossil
from MaKaC.fossils.conference import IConferenceMinimalFossil
from MaKaC.common.Conversion import Conversion


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



class ICSBookingBaseConfModifFossil(ICSBookingBaseFossil):

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

    def hasCheckStatus(self):
        """ Returns if this booking belongs to a plugin who has a "check status" concept. """

    def hasAcceptReject(self):
        """ Returns if this booking belongs to a plugin who has a "accept or reject" concept. """

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
    getConference.result = IConferenceMinimalFossil

    def getModificationURL(self):
        pass
    getModificationURL.name = "modificationURL"
    getModificationURL.convert = lambda url: str(url)



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
    getResults.result = ICSBookingBaseIndexingFossil

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
