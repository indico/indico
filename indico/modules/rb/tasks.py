# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from __future__ import unicode_literals

from datetime import datetime

from celery.schedules import crontab

from indico.core.celery import celery
from indico.core.config import Config
from indico.core.db import db
from indico.modules.rb import rb_settings, logger
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import Reservation, RepeatFrequency
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.notifications.reservation_occurrences import notify_upcoming_occurrence


@celery.periodic_task(name='roombooking_occurrences', run_every=crontab(minute='15', hour='8'))
def roombooking_occurrences():
    if not Config.getInstance().getIsRoomBookingActive():
        logger.info('Notifications not sent because room booking is disabled')
        return
    if not rb_settings.get('notifications_enabled'):
        logger.info('Notifications not sent because they are globally disabled')
        return

    # TODO: adapt this
    raise NotImplementedError('needs to be updated')

    occurrences = ReservationOccurrence.find(
        Room.is_active,
        Room.notifications_enabled,
        Reservation.is_accepted,
        Reservation.repeat_frequency != RepeatFrequency.WEEK,
        ReservationOccurrence.is_valid,
        ReservationOccurrence.start_dt >= datetime.now(),
        ~ReservationOccurrence.notification_sent,
        # TODO: filter for notification delay
        # TODO: proper sqlalchemy instead of find()
        _join=[Reservation, Room]
    )

    try:
        for occ in occurrences:
            notify_upcoming_occurrence(occ)
            occ.notification_sent = True
            if occ.reservation.repeat_frequency == RepeatFrequency.DAY:
                occ.reservation.occurrences.update({'notification_sent': True})
    finally:
        db.session.commit()
