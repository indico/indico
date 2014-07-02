from datetime import datetime, timedelta

from sqlalchemy.sql import func, cast
from sqlalchemy import Date

from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.reservations import Reservation, RepeatUnit
from indico.modules.rb.models.rooms import Room
from indico.modules.rb.models.utils import getRoomBookingOption
from indico.modules.rb.notifications.reservation_occurrences import notify_upcoming_occurrence
from indico.modules.scheduler.tasks.periodic import PeriodicUniqueTask


class OccurrenceNotifications(PeriodicUniqueTask):
    def run(self):
        if getRoomBookingOption('notificationHour') != datetime.now().hour:
            return

        today = cast(func.now(), Date)
        occurrences = ReservationOccurrence.find(
            Reservation.is_confirmed,
            ~ReservationOccurrence.is_sent,
            ReservationOccurrence.is_valid,
            cast(ReservationOccurrence.start, Date) - Room.notification_for_start * timedelta(days=1) == today,
            _join=[Reservation, Room]
        )

        for occ in occurrences:
            occ.is_sent = True
            if occ.reservation.repeat_unit == RepeatUnit.DAY:
                occ.reservation.occurrences.update({'is_sent': True})
            notify_upcoming_occurrence(occ)
