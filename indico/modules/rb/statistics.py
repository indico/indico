from __future__ import division

from datetime import date, datetime

from dateutil.relativedelta import relativedelta

from indico.core.db import db
from indico.util.date_time import iterdays
from indico.modules.rb.models.locations import Location
from indico.modules.rb.models.reservations import Reservation
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence


def calculate_rooms_bookable_time(rooms, start_date=None, end_date=None):
    if end_date is None:
        end_date = date.today() - relativedelta(days=1)
    if start_date is None:
        start_date = end_date - relativedelta(days=29)
    working_time_per_day = sum((datetime.combine(date.today(), end) - datetime.combine(date.today(), start)).seconds
                               for start, end in Location.working_time_periods)
    working_days = sum(1 for __ in iterdays(start_date, end_date, skip_weekends=True))
    return working_days * working_time_per_day * len(rooms)


def calculate_rooms_booked_time(rooms, start_date=None, end_date=None):
    if end_date is None:
        end_date = date.today() - relativedelta(days=1)
    if start_date is None:
        start_date = end_date - relativedelta(days=29)
    # Reservations on working days
    reservations = Reservation.find(Reservation.room_id.in_(r.id for r in rooms),
                                    db.extract('dow', ReservationOccurrence.start_dt).between(1, 5),
                                    ReservationOccurrence.start_dt >= start_date,
                                    ReservationOccurrence.end_dt <= end_date,
                                    ReservationOccurrence.is_valid,
                                    _join=ReservationOccurrence)

    rsv_start = db.cast(ReservationOccurrence.start_dt, db.TIME)
    rsv_end = db.cast(ReservationOccurrence.end_dt, db.TIME)
    slots = ((db.cast(start, db.TIME), db.cast(end, db.TIME)) for start, end in Location.working_time_periods)

    # this basically handles all possible ways an occurrence overlaps with each one of the working time slots
    overlaps = sum(db.case([
                ((rsv_start < start) & (rsv_end > end), db.extract('epoch', end - start)),
                ((rsv_start < start) & (rsv_end > start) & (rsv_end <= end), db.extract('epoch', rsv_end - start)),
                ((rsv_start >= start) & (rsv_start < end) & (rsv_end > end), db.extract('epoch', end - rsv_start)),
                ((rsv_start >= start) & (rsv_end <= end), db.extract('epoch', rsv_end - rsv_start))
            ], else_=0) for start, end in slots)

    return reservations.with_entities(db.func.sum(overlaps)).scalar() or 0


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
