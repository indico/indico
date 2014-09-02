from datetime import datetime

from indico.core.db import db
from indico.modules.rb import settings
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import Reservation, RepeatFrequency
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.notifications.reservation_occurrences import notify_upcoming_occurrence
from indico.modules.scheduler.tasks.periodic import PeriodicUniqueTask


def _build_notification_window_filter():
    if datetime.now().hour >= settings.get('notification_hour', 6):
        return ReservationOccurrence.is_in_notification_window()
    else:
        return ReservationOccurrence.is_in_notification_window(delayed_only=True)


class OccurrenceNotifications(PeriodicUniqueTask):
    DISABLE_ZODB_HOOK = True

    def run(self):
        occurrences = ReservationOccurrence.find(
            Reservation.is_accepted,
            ~ReservationOccurrence.notification_sent,
            ReservationOccurrence.is_valid,
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
