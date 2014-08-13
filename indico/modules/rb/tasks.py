from datetime import datetime

from sqlalchemy.sql import func, cast
from sqlalchemy import Date

from indico.modules.rb import settings
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import Reservation, RepeatFrequency
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.notifications.reservation_occurrences import notify_upcoming_occurrence
from indico.modules.scheduler.tasks.periodic import PeriodicUniqueTask


def _build_notification_before_days_filter(notification_before_days):
    days_until_occurrence = cast(ReservationOccurrence.start_dt, Date) - cast(func.now(), Date)
    notification_before_days = func.coalesce(Room.notification_for_start, notification_before_days)
    if datetime.now().hour >= settings.get('notification_hour', 6):
        # Notify of today and delayed occurrences (happening in N or less days)
        return days_until_occurrence <= notification_before_days
    else:
        # Notify only of delayed occurrences (happening in less than N days)
        return days_until_occurrence < notification_before_days


class OccurrenceNotifications(PeriodicUniqueTask):
    def run(self):
        occurrences = ReservationOccurrence.find(
            Reservation.is_accepted,
            ~ReservationOccurrence.notification_sent,
            ReservationOccurrence.is_valid,
            ReservationOccurrence.start_dt >= func.now(),
            _build_notification_before_days_filter(settings.get('notification_before_days', 0)),
            _join=[Reservation, Room]
        )

        for occ in occurrences:
            occ.notification_sent = True
            if occ.reservation.repeat_frequency == RepeatFrequency.DAY:
                occ.reservation.occurrences.update({'notification_sent': True})
            notify_upcoming_occurrence(occ)
