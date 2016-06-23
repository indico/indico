# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from collections import defaultdict
from datetime import datetime, date

from celery.schedules import crontab

from indico.core.celery import celery
from indico.core.config import Config
from indico.core.db import db
from indico.modules.rb import settings as rb_settings
from indico.modules.rb import logger
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import Reservation, RepeatFrequency
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.notifications.reservation_occurrences import (notify_upcoming_occurrence,
                                                                     notify_reservation_digest)
from indico.util.date_time import get_month_end, round_up_month


def _build_notification_window_filter():
    if datetime.now().hour >= rb_settings.get('notification_hour'):
        # Both today and delayed notifications
        return ReservationOccurrence.is_in_notification_window()
    else:
        # Delayed notifications only
        return ReservationOccurrence.is_in_notification_window(exclude_first_day=True)


def _build_digest_window_filter():
    if datetime.now().hour >= rb_settings.get('notification_hour'):
        # Both today and delayed digests
        return Room.is_in_digest_window()
    else:
        # Delayed digests only
        return Room.is_in_digest_window(exclude_first_day=True)


@celery.periodic_task(name='roombooking_occurrences_digest', run_every=crontab(minute='15', hour='8'))
def roombooking_occurrences_digest():
    if not Config.getInstance().getIsRoomBookingActive():
        logger.info('Digest not sent because room booking is disabled')
        return
    if not rb_settings.get('notifications_enabled'):
        logger.info('Digest not sent because notifications are globally disabled')
        return

    digest_start = round_up_month(date.today(), from_day=2)
    digest_end = get_month_end(digest_start)

    occurrences = ReservationOccurrence.find(
        Room.is_active,
        Room.notifications_enabled,
        Reservation.is_accepted,
        Reservation.repeat_frequency == RepeatFrequency.WEEK,
        ReservationOccurrence.is_valid,
        ReservationOccurrence.start_dt >= digest_start,
        ReservationOccurrence.start_dt <= digest_end,
        ~ReservationOccurrence.notification_sent,
        _build_digest_window_filter(),
        _join=[Reservation, Room]
    )

    digests = defaultdict(list)
    for occurrence in occurrences:
        digests[occurrence.reservation].append(occurrence)

    try:
        for reservation, occurrences in digests.iteritems():
            notify_reservation_digest(reservation, occurrences)
            for occurrence in occurrences:
                occurrence.notification_sent = True
    finally:
        db.session.commit()


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
        Reservation.repeat_frequency != RepeatFrequency.WEEK,
        ReservationOccurrence.is_valid,
        ReservationOccurrence.start_dt >= datetime.now(),
        ~ReservationOccurrence.notification_sent,
        _build_notification_window_filter(),
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
