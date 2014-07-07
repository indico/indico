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


from MaKaC.conference import Contribution
from MaKaC.plugins.Collaboration.base import CSBookingBase
from MaKaC.plugins.Collaboration.WebcastRequest.mail import NewRequestNotification, RequestModifiedNotification, RequestDeletedNotification,\
    RequestRejectedNotification, RequestAcceptedNotification,\
    RequestAcceptedNotificationAdmin, RequestRejectedNotificationAdmin,\
    RequestRescheduledNotification, RequestRelocatedNotification
from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
from MaKaC.common.mail import GenericMailer
from MaKaC.plugins.Collaboration.WebcastRequest.common import WebcastRequestError
from MaKaC.common.logger import Logger
from MaKaC.plugins.Collaboration.collaborationTools import MailTools
from indico.core.index import Catalog
from MaKaC.i18n import _

class CSBooking(CSBookingBase):

    _hasStart = False
    _hasStop = False
    _hasCheckStatus = True
    _hasAcceptReject = True

    _needsBookingParamsCheck = True

    _allowMultiple = False

    _hasStartDate = False

    _commonIndexes = ["All Requests"]

    _simpleParameters = {
        "talks" : (str, ''),
        "talkSelection": (list, []),
        "otherComments": (str, ''),
        "audience": (str, '')}

    def __init__(self, type, conf):
        CSBookingBase.__init__(self, type, conf)

    def _checkBookingParams(self):
        return False

    def getStatusMessage(self):
        return self._statusMessage

    def getStatusClass(self):
        return self._statusClass

    def hasHappened(self):
        return False

    def isHappeningNow(self):
        return False

    def _create(self):
        self._statusMessage = "Request successfully sent"
        self._statusClass = "statusMessageOther"

        if MailTools.needToSendEmails('WebcastRequest'):
            try:
                notification = NewRequestNotification(self)
                GenericMailer.sendAndLog(notification, self.getConference(),
                                         self.getPlugin().getName())
            except Exception,e:
                Logger.get('RecReq').exception(
                    """Could not send NewRequestNotification for request with id %s of event %s, exception: %s""" % (self._id, self.getConference().getId(), str(e)))
                return WebcastRequestError('create', e)


    def _modify(self, oldBookingParams):
        self._statusMessage = "Request successfully sent"
        self._statusClass = "statusMessageOther"

        if MailTools.needToSendEmails('WebcastRequest'):
            try:
                notification = RequestModifiedNotification(self)
                GenericMailer.sendAndLog(notification, self.getConference(),
                                         self.getPlugin().getName())
            except Exception,e:
                Logger.get('RecReq').exception(
                    """Could not send RequestModifiedNotification for request with id %s of event %s, exception: %s""" % (self._id, self.getConference().getId(), str(e)))
                return WebcastRequestError('edit', e)


    def _checkStatus(self):
        pass

    def _accept(self, user = None):
        self._statusMessage = "Request accepted"
        self._statusClass = "statusMessageOK"
        import MaKaC.webcast as webcast
        webcast.HelperWebcastManager.getWebcastManagerInstance().addForthcomingWebcast(self._conf, self._bookingParams.get("audience", ""))

        try:
            notification = RequestAcceptedNotification(self)
            GenericMailer.sendAndLog(notification, self.getConference(),
                                     self.getPlugin().getName())
        except Exception,e:
            Logger.get('RecReq').exception(
                """Could not send RequestAcceptedNotification for request with id %s of event %s, exception: %s""" % (self._id, self.getConference().getId(), str(e)))
            return WebcastRequestError('accept', e)

        if MailTools.needToSendEmails('WebcastRequest'):
            try:
                notification = RequestAcceptedNotificationAdmin(self, user)
                GenericMailer.sendAndLog(notification, self.getConference(),
                                         self.getPlugin().getName())
            except Exception,e:
                Logger.get('RecReq').exception(
                    """Could not send RequestAcceptedNotificationAdmin for request with id %s of event %s, exception: %s""" % (self._id, self.getConference().getId(), str(e)))
                return WebcastRequestError('accept', e)

        manager = Catalog.getIdx("cs_bookingmanager_conference").get(self._conf.getId())
        manager.notifyInfoChange()

    def _reject(self):
        self._statusMessage = "Request rejected by responsible"
        self._statusClass = "statusMessageError"
        import MaKaC.webcast as webcast
        webcast.HelperWebcastManager.getWebcastManagerInstance().delForthcomingWebcast(self._conf)

        try:
            notification = RequestRejectedNotification(self)
            GenericMailer.sendAndLog(notification, self.getConference(),
                                     self.getPlugin().getName())
        except Exception,e:
            Logger.get('RecReq').exception(
                """Could not send RequestRejectedNotification for request with id %s of event %s, exception: %s""" % (self._id, self.getConference().getId(), str(e)))
            return WebcastRequestError('reject', e)

        if MailTools.needToSendEmails('WebcastRequest'):
            try:
                notification = RequestRejectedNotificationAdmin(self)
                GenericMailer.sendAndLog(notification, self.getConference(),
                                         self.getPlugin().getName())
            except Exception,e:
                Logger.get('RecReq').exception(
                    """Could not send RequestRejectedNotificationAdmin for request with id %s of event %s, exception: %s""" % (self._id, self.getConference().getId(), str(e)))
                return WebcastRequestError('reject', e)

    def _delete(self):
        import MaKaC.webcast as webcast
        webcast.HelperWebcastManager.getWebcastManagerInstance().delForthcomingWebcast(self._conf)

        if MailTools.needToSendEmails('WebcastRequest'):
            try:
                notification = RequestDeletedNotification(self)
                GenericMailer.sendAndLog(notification, self.getConference(),
                                         self.getPlugin().getName())
            except Exception,e:
                Logger.get('RecReq').exception(
                    """Could not send RequestDeletedNotification for request with id %s of event %s, exception: %s""" % (self._id, self.getConference().getId(), str(e)))
                return WebcastRequestError('remove', e)

    def notifyEventDateChanges(self, oldStartDate, newStartDate, oldEndDate, newEndDate):
        manager = Catalog.getIdx("cs_bookingmanager_conference").get(self._conf.getId())
        manager._changeConfStartDateInIndex(self, oldStartDate, newStartDate)
        if MailTools.needToSendEmails('WebcastRequest'):
            try:
                notification = RequestRescheduledNotification(self)
                GenericMailer.sendAndLog(notification, self.getConference(),
                                         self.getPlugin().getName())
            except Exception,e:
                Logger.get('RecReq').exception(
                    """Could not send RequestRescheduledNotification for request with id %s of event %s, exception: %s""" % (self._id, self.getConference().getId(), str(e)))
                return WebcastRequestError('edit', e)

    def notifyLocationChange(self):
        self.unindex_instances()
        self.index_instances()
        if MailTools.needToSendEmails('WebcastRequest'):
            try:
                notification = RequestRelocatedNotification(self)
                GenericMailer.sendAndLog(notification, self.getConference(),
                                         self.getPlugin().getName())
            except Exception,e:
                Logger.get('RecReq').exception(
                    """Could not send RequestRelocatedNotification for request with id %s of event %s, exception: %s""" % (self._id, self.getConference().getId(), str(e)))
                return WebcastRequestError('edit', e)

    def index_instances(self):
        idx = Catalog.getIdx('cs_booking_instance')
        idx['WebcastRequest'].index_booking(self)
        idx['All Requests'].index_booking(self)

    def unindex_instances(self):
        idx = Catalog.getIdx('cs_booking_instance')
        idx['WebcastRequest'].unindex_booking(self)
        idx['All Requests'].unindex_booking(self)

    def index_talk(self, talk):
        if CollaborationTools.isAbleToBeWebcastOrRecorded(talk, "WebcastRequest") and self.isChooseTalkSelected() \
                and self.getTalkSelectionList() and talk.getId() in self.getTalkSelectionList():
            idx = Catalog.getIdx('cs_booking_instance')
            idx['WebcastRequest'].index_talk(self, talk)
            idx['All Requests'].index_talk(self, talk)

    def unindex_talk(self, talk):
        idx = Catalog.getIdx('cs_booking_instance')
        idx['WebcastRequest'].unindex_talk(self, talk)
        idx['All Requests'].unindex_talk(self, talk)

    def notifyDeletion(self, obj):
        # The talk is unindexed if it is a Contribution and it has startDate
        if isinstance(obj, Contribution) and obj.getStartDate() is not None:
            self.unindex_talk(obj)
