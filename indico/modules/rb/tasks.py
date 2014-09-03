from collections import defaultdict
from datetime import datetime, date

from indico.core.db import db
from indico.modules.rb import settings
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import Reservation, RepeatFrequency
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.notifications.reservation_occurrences import (notify_upcoming_occurrence,
                                                                     notify_reservation_digest)
from indico.modules.scheduler.tasks.periodic import PeriodicUniqueTask
from indico.util.date_time import get_month_end, round_up_month


def _build_notification_window_filter():
    if datetime.now().hour >= settings.get('notification_hour', 6):
        # Both today and delayed notifications
        return ReservationOccurrence.is_in_notification_window()
    else:
        # Delayed notifications only
        return ReservationOccurrence.is_in_notification_window(exclude_first_day=True)


def _build_digest_window_filter():
    if datetime.now().hour >= settings.get('notification_hour', 6):
        # Both today and delayed digests
        return Room.is_in_digest_window()
    else:
        # Delayed digests only
        return Room.is_in_digest_window(exclude_first_day=True)


class OccurrenceDigest(PeriodicUniqueTask):
    DISABLE_ZODB_HOOK = True

    def run(self):
        digest_start = round_up_month(date.today(), from_day=2)
        digest_end = get_month_end(digest_start)

        occurrences = ReservationOccurrence.find(
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


class OccurrenceNotifications(PeriodicUniqueTask):
    DISABLE_ZODB_HOOK = True

    def run(self):
        occurrences = ReservationOccurrence.find(
            Reservation.is_accepted,
            Reservation.repeat_frequency != RepeatFrequency.WEEK,
            ReservationOccurrence.is_valid,
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
