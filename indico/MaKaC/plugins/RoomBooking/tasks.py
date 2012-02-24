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

from MaKaC.plugins.base import Observable
from MaKaC.rb_location import ReservationGUID

from indico.modules.scheduler.tasks import OneShotTask, PeriodicUniqueTask


class RoomReservationEndTask(OneShotTask, Observable):
    def __init__(self, resv, endDT, occurrence):
        super(RoomReservationEndTask, self).__init__(endDT)
        self.resvGUID = str(resv.guid)
        self.resvOccurrence = occurrence

    def run(self):
        resv = ReservationGUID.parse(self.resvGUID).getReservation()
        if not resv:
            self.getLogger().info('Reservation %r does not exist anymore, not triggering end notification' % self.resvGUID)
            return
        elif self._resv.isCancelled:
            self.getLogger().info('Reservation %s is cancelled, no email will be sent' % resv.guid)
            return
        elif self._resv.isRejected:
            self.getLogger().info('Reservation %s is rejected, no email will be sent' % resv.guid)
            return
        elif not self._resv.isConfirmed:
            self.getLogger().info('Reservation %s is not confirmed, no email will be sent' % resv.guid)
            return
        elif resv.dayIsExcluded(self.resvOccurrence.startDT.date()):
            self.getLogger().info('Occurrence %s is excluded (rejected or cancelled)' % self.resvOccurrence)
            return
        resv.getStartEndNotification().sendEndNotification(self.resvOccurrence)


class RoomReservationTask(PeriodicUniqueTask):
    """
    Sends room reservation start notifications.
    Also takes care of creating the end notification task.
    """

    def run(self):
        from MaKaC.plugins.RoomBooking.notifications import sendStartNotifications
        sendStartNotifications(self.getLogger())
