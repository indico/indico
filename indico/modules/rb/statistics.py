from __future__ import division

from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta
from sqlalchemy import func, extract, cast, TIME

from indico.core.db.sqlalchemy.custom import greatest, least
from indico.util.date_time import iterdays
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.reservations import Reservation
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence


def calculate_rooms_bookable_time(rooms, start_date=None, end_date=None):
    if end_date is None:
        end_date = date.today() - relativedelta(days=1)
    if start_date is None:
        start_date = end_date - relativedelta(days=29)
    working_time_start = datetime.combine(date.today(), Location.working_time_start)
    working_time_end = datetime.combine(date.today(), Location.working_time_end)
    working_time_per_day = (working_time_end - working_time_start).seconds
    working_days = sum(1 for __ in iterdays(start_date, end_date, skip_weekends=True))
    return working_days * working_time_per_day * len(rooms)


def calculate_rooms_booked_time(rooms, start_date=None, end_date=None):
    if end_date is None:
        end_date = date.today() - relativedelta(days=1)
    if start_date is None:
        start_date = end_date - relativedelta(days=29)
    # Reservations on working days
    reservations = Reservation.find(Reservation.room_id.in_(r.id for r in rooms),
                                    extract('dow', ReservationOccurrence.start_dt).between(1, 5),
                                    ReservationOccurrence.start_dt >= start_date,
                                    ReservationOccurrence.end_dt <= end_date,
                                    ReservationOccurrence.is_valid,
                                    _join=ReservationOccurrence)
    # Take into account only working hours
    earliest_time = greatest(cast(ReservationOccurrence.start_dt, TIME), Location.working_time_start)
    latest_time = least(cast(ReservationOccurrence.end_dt, TIME), Location.working_time_end)
    booked_time = reservations.with_entities(func.sum(latest_time - earliest_time)).scalar()
    return (booked_time or timedelta()).total_seconds()


def calculate_rooms_occupancy(rooms, start=None, end=None):
    bookable_time = calculate_rooms_bookable_time(rooms, start, end)
    booked_time = calculate_rooms_booked_time(rooms, start, end)
    return booked_time / bookable_time if bookable_time else 0


def compose_rooms_stats(rooms):
    reservations = Reservation.find(Reservation.room_id.in_(r.id for r in rooms))
    return {
        'active': {
            'valid': reservations.filter(Reservation.is_valid, ~Reservation.is_archived).count(),
            'pending': reservations.filter(Reservation.is_pending, ~Reservation.is_archived).count(),
            'cancelled': reservations.filter(Reservation.is_cancelled, ~Reservation.is_archived).count(),
            'rejected': reservations.filter(Reservation.is_rejected, ~Reservation.is_archived).count(),
        },
        'archived': {
            'valid': reservations.filter(Reservation.is_valid, Reservation.is_archived).count(),
            'pending': reservations.filter(Reservation.is_pending, Reservation.is_archived).count(),
            'cancelled': reservations.filter(Reservation.is_cancelled, Reservation.is_archived).count(),
            'rejected': reservations.filter(Reservation.is_rejected, Reservation.is_archived).count()
        }
    }
