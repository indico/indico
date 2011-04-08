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
from indico.core.api.reservation import IReservationListener, IReservationStartStopListener
from indico.core.api.base import Component
from zope.interface import implements
from datetime import datetime, timedelta
from persistent import Persistent
from modules.scheduler.client import Client
from modules.scheduler import tasks
from MaKaC.plugins.base import Observable, PluginsHolder
from MaKaC.webinterface.wcomponents import WTemplated
from MaKaC.common.utils import getEmailList, formatDateTime
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.common.mail import GenericMailer
from MaKaC.webinterface.mail import GenericNotification
from MaKaC.plugins.RoomBooking.common import getRoomBookingOption
from MaKaC.webinterface import urlHandlers

class ReservationStartEndNotificationListener(Component):
    implements(IReservationListener)

    def reservationCreated(self, resv):
        if getRoomBookingOption('notificationEnabled'):
            resv.getStartEndNotification().resvCreated()

    def reservationUpdated(self, resv):
        if getRoomBookingOption('notificationEnabled'):
            resv.getStartEndNotification().resvUpdated()

    def reservationDeleted(self, resv):
        pass

class ReservationStartEndEmailListener(Component):
    implements(IReservationStartStopListener)

    def reservationStarted(self, obj, resv):
        sendReservationStartStopNotification(resv, 'start')

    def reservationFinished(self, obj, resv):
        sendReservationStartStopNotification(resv, 'end')

def sendReservationStartStopNotification(resv, which):
    if which == 'start' and resv.room.resvStartNotification:
        msg = getRoomBookingOption('startNotificationEmail')
        subject = getRoomBookingOption('startNotificationEmailSubject')
    elif which == 'end' and resv.room.resvEndNotification:
        msg = getRoomBookingOption('endNotificationEmail')
        subject = getRoomBookingOption('endNotificationEmailSubject')
    else:
        return

    av = resv.bookedForUser
    if av:
        bookedForDetails = '%s %s\n%s' % (av.getFullName(), av.getPersonId() or '', av.getEmail())
    else:
        bookedForDetails = '%s\n%s' % (resv.bookedForName, resv.contactEmail)

    msgArgs = {
        'bookedForUser': bookedForDetails,
        'roomName': resv.room.getFullName(),
        'roomAtts': resv.room.customAtts,
        'bookingStart': formatDateTime(resv.startDT),
        'bookingEnd': formatDateTime(resv.endDT),
        'detailsLink': urlHandlers.UHRoomBookingBookingDetails.getURL(resv)
    }

    recipients = []
    recipients += getRoomBookingOption('notificationEmails')
    if getRoomBookingOption('notificationEmailsToBookedFor'):
        recipients += getEmailList(resv.contactEmail)
    maildata = {
        'fromAddr': HelperMaKaCInfo.getMaKaCInfoInstance().getNoReplyEmail(returnSupport=True),
        'toList': recipients,
        'subject': subject.format(**msgArgs),
        'body': msg.format(**msgArgs)
    }
    GenericMailer.send(GenericNotification(maildata))

class ReservationStartEndNotification(Persistent, Observable):

    def __init__(self, resv):
        minutes = getRoomBookingOption('notificationBefore')
        self._notificationBefore = timedelta(minutes=minutes)
        self._startActionTriggered = False
        self._endActionTriggered = False
        self._resv = resv
        self._startDT = self._resv.getLocalizedStartDT() - self._notificationBefore
        self._endDT = self._resv.getLocalizedEndDT()
        self._hasTasks = False

    def resvCreated(self):
        if self._resv.endDT > datetime.now():
            self.createTasks()

    def resvUpdated(self):
        #self._startActionTriggered = self._endActionTriggered = False # XXX REMOVE THIS LATER XXX
        # Event was created in the past and is still in the past -> don't do anything
        if not self._hasTasks and self._resv.endDT <= datetime.now():
            return
        if self._startDT != self._resv.getLocalizedStartDT() - self._notificationBefore:
            self._startDT = self._resv.getLocalizedStartDT() - self._notificationBefore
            if self._endActionTriggered:
                if self._resv.startDT > datetime.now():
                    # If the booking had finished but it was changed to start in the future, we can safely re-execute both actions
                    self._startActionTriggered = False
                    self._endActionTriggered = False
                # In any other case we don't need to change flags
            if not self._startActionTriggered:
                self.createTasks('start')
        if self._endDT != self._resv.getLocalizedEndDT() or not self._hasTasks:
            self._endDT = self._resv.getLocalizedEndDT()
            if not self._endActionTriggered:
                self.createTasks('end')

    def createTasks(self, which=None):
        # We cannot get an ID for the task here and since RB can use a separate DB we also cannot store the task itself in the DB.
        # So we have no way of modifying/removing our task when the booking is updated/cancelled/rejected.
        # Instead we always add a new task and the task checks if it's valid when being executed
        # If a notification has been sent before, we don't send a new one (e.g. if someone changes the end time of an expired event)
        self._hasTasks = True
        cl = Client()
        if not which or which == 'start':
            cl.enqueue(tasks.RoomReservationStartedTask(self._resv, self._startDT))
        if not which or which == 'end':
            cl.enqueue(tasks.RoomReservationFinishedTask(self._resv, self._endDT))

    def taskTriggered(self, which, task):
        if not self._shouldTriggerActions(task.getStartOn(), which, task.getLogger()):
            return
        if which == 'start':
            self._notify('reservationStarted', self._resv)
        elif which == 'end' and self.isActionTriggered('start'):
            self._notify('reservationFinished', self._resv)
        self.actionTriggered(which)

    def _shouldTriggerActions(self, now, which, logger):
        if which == 'start' and self._startDT != now:
            logger.info('Reservation %s did not start yet (%s != %s), not triggering actions' % (self._resv.guid, self._startDT, now))
            return False
        elif which == 'end' and self._endDT != now:
            logger.info('Reservation %s did not finish yet (%s != %s), not triggering actions' % (self._resv.guid, self._endDT, now))
            return False
        elif self.isActionTriggered(which):
            logger.info('Reservation %s already had its %s actions sent, not triggering actions' % (self._resv.guid, which))
            return False
        return True

    def actionTriggered(self, which):
        if which == 'start':
            self._startActionTriggered = True
        elif which == 'end':
            self._endActionTriggered = True

    def isActionTriggered(self, which):
        if which == 'start':
            return self._startActionTriggered
        elif which == 'end':
            return self._endActionTriggered





