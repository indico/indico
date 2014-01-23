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

from MaKaC.plugins.base import ActionBase
from MaKaC.i18n import _
from MaKaC.plugins.Collaboration.Vidyo.common import VidyoTools, VidyoError,\
    getVidyoOptionValue
from MaKaC.plugins.Collaboration.Vidyo.pages import WShowOldRoomIndexActionResult,\
    WDeleteOldRoomsActionResult
from MaKaC.plugins.Collaboration.collaborationTools import MailTools
from MaKaC.common.mail import GenericMailer
from MaKaC.common.logger import Logger
from MaKaC.plugins.Collaboration.Vidyo.mail import VidyoCleaningDoneNotification
from MaKaC.conference import CategoryManager, ConferenceHolder
from indico.core.index import Catalog
from MaKaC.user import AvatarHolder
from MaKaC.common.timezoneUtils import nowutc
from datetime import timedelta

pluginActions = [
    ("deleteOldRooms", {"buttonText": "Delete old Vidyo rooms",
                        "associatedOption": "cleanWarningAmount"}),
    ("showOldRoomIndex", {"buttonText": "Preview the cleanup operation",
                          "associatedOption": "cleanWarningAmount"}),
    ("cleanOldRoomIndex", {"buttonText": "Clean the old room index",
                          "associatedOption": "cleanWarningAmount",
                          "visible": False}),
    ("testCreateLotsOfBookings", {"buttonText": "Create lots of bookings",
                          "associatedOption": "cleanWarningAmount",
                          "visible": False}),
    ("testDeleteLotsOfBookings", {"buttonText": "Delete lots of bookings",
                          "associatedOption": "cleanWarningAmount",
                          "visible": False}),
    ("clearWSDLCache", {"buttonText": "Clear WSDL Cache. Use when WSDL has changed",
                        "associatedOption": "sudsCacheLocation"})
]

class DeleteOldRoomsAction(ActionBase):

    @classmethod
    def _deleteRemoteRooms(cls, maxDate):
        """ Deletes the remote rooms from Vidyo
            Ignores if a room does not exist (because booking._delete does not return VidyoError in that case).
            Stops in any other error / exception and returns the error cause and attainedDate-
            booking._delete will execute the remote deletion for 1 room wrapped with ExternalOperationsManager
        """
        error = False
        attainedDate = None
        try:
            for booking in list(VidyoTools.getEventEndDateIndex().iterbookings(maxDate = maxDate)):
                result = booking._delete(fromDeleteOld = True, maxDate = maxDate)
                if isinstance(result, VidyoError):
                    error = result
                    attainedDate = booking.getConference().getAdjustedEndDate(tz = 'UTC')
                    break
        except Exception, e:
            error = e
            attainedDate = booking.getConference().getAdjustedEndDate(tz = 'UTC')

        return error, attainedDate

    @classmethod
    def _sendResultEmail(cls, maxDate, previousTotal, newTotal, error, attainedDate):
        """ Sends a mail detailing how the operation went
        """
        if MailTools.needToSendEmails('Vidyo'):
            try:
                notification = VidyoCleaningDoneNotification(maxDate, previousTotal, newTotal, error, attainedDate)
                GenericMailer.send(notification)
            except Exception, e:
                Logger.get('Vidyo').error(
                    """Could not send VidyoCleaningDoneNotification, exception: %s""" % str(e))

    def call(self):
        try:
            maxDate = VidyoTools.getBookingsOldDate()
            previousTotal = VidyoTools.getEventEndDateIndex().getCount()

            error, attainedDate = DeleteOldRoomsAction._deleteRemoteRooms(maxDate)

            newTotal = VidyoTools.getEventEndDateIndex().getCount()

            page = WDeleteOldRoomsActionResult(maxDate, previousTotal, newTotal, error, attainedDate).getHTML()

            #we send the mail without ExternalOperationsManager wrapping so that we see the result of an
            #eventual 2nd pass (we do want to have more than 1 email, or at least the last one)
            #TODO: change later when emails are stored in ContextManager and sent after commit
            DeleteOldRoomsAction._sendResultEmail(maxDate, previousTotal, newTotal, error, attainedDate)

            return page

        except Exception:
            Logger.get("Vidyo").exception("Exception during Vidyo's DeleteOldRoomsAction call")
            raise


class ShowOldRoomIndexAction(ActionBase):

    def call(self):
        maxDate = VidyoTools.getBookingsOldDate()
        return WShowOldRoomIndexActionResult(maxDate).getHTML()

class ClearWSDLCacheAction(ActionBase):

    def call(self):
        """ We try to clear the persistent, file-based cache.
            In Linux it's located in /tmp/suds
        """
        cacheLocation = getVidyoOptionValue("sudsCacheLocation").strip()
        if cacheLocation:
            import os.path
            if os.path.isdir(cacheLocation):
                import shutil
                shutil.rmtree(cacheLocation)
                return _("The cache directory: ") + cacheLocation + _(" has been deleted")
            else:
                return _("The cache location supplied: ") + cacheLocation + _(" does not exist or is not a directory")
        else:
            return _("No cache location was defined. Nothing to clean")

##########################################################
# Actions only for developing or testing purposes
# make them visible and change the xrange parameters for
# them to work.
##########################################################

class CleanOldRoomIndexAction(ActionBase):
    """ Warning! only use for developing purposes.
    """

    def call(self):
        VidyoTools.getEventEndDateIndex().clear()


class TestCreateLotsOfBookingsAction(ActionBase):
    """ Warning! Before creating the conferences and the bookings,
        you probably want to comment the lines in collaboration.py
        that actually communicate with the API.
        This should be used to test the Indico DB performance.
        Also, change the Avatar ID to a suitable one!
    """

    def call(self):
        categ1 = CategoryManager().getById('1') #target category here
        for i in xrange(1, 0 + 1): #number of conferences to create here
            c = categ1.newConference(AvatarHolder().getById('1')) #creator of event
            c.setTitle("event " + str(i))
            c.setTimezone('UTC')
            c.setDates(nowutc() - timedelta(hours = i), nowutc() - timedelta(hours = i - 1))
            for j in xrange(1, 0+1): #number of bookings per event
                Catalog.getIdx("cs_bookingmanager_conference").get(c.getId()).createBooking("Vidyo", {"roomName":"room_"+str(i)+"_"+str(j),
                                                                "roomDescription": "test",
                                                                "owner":{"_type": "Avatar", "id":"1"}})

class TestDeleteLotsOfBookingsAction(ActionBase):

    def call(self):
        """ Warning! Before creating the conferences and the bookings,
            you probably want to comment the lines in collaboration.py
            that actually communicate with the API.
            This should be used to test the Indico DB performance.
        """
        ch = ConferenceHolder()
        for i in xrange(1, 0+1): #ids of events to remove
            c = ch.getById(str(i))
            c.delete()
