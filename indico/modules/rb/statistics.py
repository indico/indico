from __future__ import division

from datetime import date, datetime, timedelta

from dateutil.relativedelta import relativedelta
from sqlalchemy import func

from indico.modules.rb.models.reservations import Reservation
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence


def calculate_rooms_bookable_time(rooms, start_date=None, end_date=None):
    if end_date is None:
        end_date = datetime.utcnow()
    if start_date is None:
        start_date = end_date + relativedelta(months=-1)

    total_days = (end_date - start_date).days + 1
    bookable_time = 0
    for room in rooms:
        bookable_time += (total_days - room.get_nonbookable_days(start_date, end_date)) * room.bookable_time_per_day

    return bookable_time


def calculate_rooms_booked_time(rooms, start_date=None, end_date=None):
    if end_date is None:
        end_date = date.today()
    if start_date is None:
        start_date = end_date + relativedelta(months=-1)

    reservations = Reservation.find(Reservation.room_id.in_(r.id for r in rooms))
    query = (reservations.join(ReservationOccurrence)
             .with_entities(func.sum(ReservationOccurrence.end - ReservationOccurrence.start))
             .filter(ReservationOccurrence.start >= start_date,
                     ReservationOccurrence.end <= end_date,
                     ReservationOccurrence.is_valid))
    return (query.scalar() or timedelta()).total_seconds()


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
