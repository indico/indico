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

from datetime import datetime
from operator import attrgetter

from celery.schedules import crontab

from indico.core.celery import celery
from indico.core.config import Config
from indico.core.db import db
from indico.modules.rb import settings as rb_settings
from indico.modules.rb import logger
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import Reservation, RepeatFrequency
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.notifications.reservation_occurrences import notify_upcoming_occurrences
from indico.modules.rb.util import first_occurrence_date


def _build_notification_window_filter():
    if datetime.now().hour >= rb_settings.get('notification_hour'):
        # Both today and delayed notifications
        return ReservationOccurrence.is_in_notification_window()
    else:
        # Delayed notifications only
        return ReservationOccurrence.is_in_notification_window(exclude_first_day=True)


@celery.periodic_task(name='roombooking_occurrences', run_every=crontab(minute='15', hour='8'))
def roombooking_occurrences():
    if not Config.getInstance().getIsRoomBookingActive():
        logger.info('Notifications not sent because room booking is disabled')
        return
    if not rb_settings.get('notifications_enabled'):
        logger.info('Notifications not sent because they are globally disabled')
        return

    occurrences = ReservationOccurrence.find(
        Room.is_active,
        Room.notifications_enabled,
        Reservation.is_accepted,
        ReservationOccurrence.is_valid,
        ReservationOccurrence.start_dt >= datetime.now(),
        ~ReservationOccurrence.notification_sent,
        _build_notification_window_filter(),
        _join=[Reservation, Room]
    )

    try:
        for occ in occurrences:
            same_user_occurrences = []
            for other in occurrences:
                if (other.reservation.booked_for_user == occ.reservation.booked_for_user and
                        first_occurrence_date(other) == first_occurrence_date(occ) and not other.notification_sent):
                    other.notification_sent = True
                    if other.reservation.repeat_frequency == RepeatFrequency.DAY:
                        other.reservation.occurrences.update({'notification_sent': True})
                    same_user_occurrences.append(other)
            if not same_user_occurrences:
                continue
            same_user_occurrences = sorted(same_user_occurrences, key=attrgetter('start_dt'))
            notify_upcoming_occurrences(same_user_occurrences)
    finally:
        db.session.commit()
