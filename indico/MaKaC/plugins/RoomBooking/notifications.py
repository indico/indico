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

from zope.interface import implements
from datetime import datetime, timedelta, date, time
from persistent import Persistent
from itertools import ifilter
from MaKaC.plugins.base import Observable, PluginsHolder
from MaKaC.webinterface.wcomponents import WTemplated
from MaKaC.common.utils import getEmailList, formatDateTime
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.common.mail import GenericMailer
from MaKaC.webinterface.mail import GenericNotification
from MaKaC.plugins.RoomBooking.common import getRoomBookingOption
from MaKaC.plugins.RoomBooking.tasks import RoomReservationEndTask
from MaKaC.webinterface import urlHandlers
from indico.core.config import Config
from MaKaC.rb_tools import fromUTC, toUTC, Period
from MaKaC.rb_reservation import ReservationBase, RepeatabilityEnum
from MaKaC.rb_room import RoomBase
from MaKaC.common.timezoneUtils import server2utc

from indico.core.extpoint.reservation import IReservationListener, IReservationStartStopListener
from indico.core.extpoint.base import Component
from indico.modules.scheduler.client import Client
from indico.util.caching import cached_property


DEBUG = False # enable various debug prints and ignore the notification hour setting

def _getRoomSpecificNotificationBeforeDays():
    """Get the resvStartNotificationBefore for all rooms that uses notifications. """
    def _filter(r):
        return (r.resvStartNotification or r.resvEndNotification) and r.resvStartNotificationBefore is not None
    return set(r.resvStartNotificationBefore for r in ifilter(_filter, RoomBase.getRooms()))

def sendStartNotifications(logger):
    if getRoomBookingOption('notificationHour') != datetime.now().hour:
        if DEBUG:
            print 'Outside notification hour. Continuing anyway due to debug mode.'
        else:
            return
    days = _getRoomSpecificNotificationBeforeDays()
    days.add(getRoomBookingOption('notificationBefore'))
    dates = [date.today() + timedelta(days=day) for day in days]
    if DEBUG:
        print 'Dates to check: %r' % map(str, dates)
    for resv in ReservationBase.getReservations(days=dates): # for testing, remove location later
        se = resv.getStartEndNotification()
        se.sendStartNotification(logger)

def sendReservationStartStopNotification(resv, which, occurrence):
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
        'occStart': formatDateTime(occurrence.startDT),
        'occEnd': formatDateTime(occurrence.endDT),
        'detailsLink': urlHandlers.UHRoomBookingBookingDetails.getURL(resv)
    }

    recipients = set()
    recipients.update(getRoomBookingOption('notificationEmails'))
    if getRoomBookingOption('notificationEmailsToBookedFor'):
        recipients.update(getEmailList(resv.contactEmail))
    if resv.room.resvNotificationToResponsible:
        recipients.add(resv.room.getResponsible().getEmail())
    maildata = {
        'fromAddr': Config.getInstance().getNoReplyEmail(),
        'toList': list(recipients),
        'subject': subject.format(**msgArgs),
        'body': msg.format(**msgArgs)
    }
    GenericMailer.send(GenericNotification(maildata))

class ReservationStartEndNotification(Persistent, Observable):

    def __init__(self, resv):
        self._resv = resv
        self._notificationsSent = set()

    @cached_property
    def _daysBefore(self):
        roomSpecificDays = self._resv.room.resvStartNotificationBefore
        if roomSpecificDays is not None:
            return timedelta(days=roomSpecificDays)
        return timedelta(days=getRoomBookingOption('notificationBefore'))

    def sendStartNotification(self, logger):
        if self._resv.isCancelled:
            if DEBUG:
                print 'Reservation %s is cancelled, no email will be sent' % self._resv.guid
            return
        elif self._resv.isRejected:
            if DEBUG:
                print 'Reservation %s is rejected, no email will be sent' % self._resv.guid
            return
        elif not self._resv.isConfirmed:
            if DEBUG:
                print 'Reservation %s is not confirmed, no email will be sent' % self._resv.guid
            return

        # If we want to notify 2 days before, we need to go back 3 days since the
        # chosen day will *not* be checked by getNextRepeating()
        delta = self._daysBefore - timedelta(days=1)
        occurrence = self._resv.getNextRepeating(date.today() + delta)
        if not occurrence:
            return

        if self._resv.repeatability == RepeatabilityEnum.daily:
            # If the booking has daily repetition we do not want to spam people and
            # thus handle it as one occurence over the whole lifetime of the booking
            if DEBUG:
                print 'Booking has daily repetition, only considering the whole period'
            if occurrence.startDT != self._resv.startDT:
                if DEBUG:
                    print 'Occurrence is not the first one (%s != %s)' % (occurrence.startDT, self._resv.startDT)
                return
            if DEBUG:
                print 'Original occurrence: %s' % occurrence
            occurrence = Period(self._resv.startDT, self._resv.endDT)

        if occurrence.startDT.date() != date.today() + self._daysBefore:
            if DEBUG:
                print 'Occurence %s is on the wrong date' % occurrence
            return
        elif occurrence.startDT < datetime.now():
            if DEBUG:
                print 'Occurence %s already started' % occurrence
            return

        if occurrence in self._notificationsSent:
            if DEBUG:
                print 'Occurrence %s already had a notification' % occurrence
            return
        elif DEBUG:
            print 'Sending notification for occurrence: %s' % occurrence

        if self._resv.dayIsExcluded(occurrence.startDT.date()):
            if DEBUG:
                print 'Occurrence %s is excluded (rejected or cancelled)' % occurrence
            return
        self._notificationsSent.add(occurrence)
        self._p_changed = 1
        if self._resv.room.resvStartNotification:
            sendReservationStartStopNotification(self._resv, 'start', occurrence)
        if self._resv.room.resvEndNotification:
            Client().enqueue(RoomReservationEndTask(self._resv, server2utc(occurrence.endDT), occurrence))

    def sendEndNotification(self, occurrence):
        sendReservationStartStopNotification(self._resv, 'end', occurrence)

