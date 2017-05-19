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

from collections import defaultdict
from datetime import timedelta, datetime, time
from itertools import groupby
from operator import attrgetter

from flask import session
from sqlalchemy.orm import defaultload
from werkzeug.datastructures import MultiDict

from indico.modules.rb.models.blocked_rooms import BlockedRoom
from indico.modules.rb.models.room_nonbookable_periods import NonBookablePeriod
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.rb.models.rooms import Room
from indico.util.date_time import iterdays, overlaps, format_date
from indico.util.i18n import _
from indico.util.serializer import Serializer
from indico.util.string import natural_sort_key
from indico.util.struct.iterables import group_list
from indico.web.flask.util import url_for
from indico.legacy.webinterface.wcomponents import WTemplated


class RoomBookingCalendarWidget(object):
    def __init__(self, occurrences, start_dt, end_dt, candidates=None, rooms=None, specific_room=None,
                 repeat_frequency=None, repeat_interval=None, flexible_days=0, show_blockings=True):
        self.occurrences = occurrences
        self.start_dt = start_dt
        self.end_dt = end_dt
        self.candidates = candidates
        self.rooms = rooms
        self.specific_room = specific_room
        self.repeat_frequency = repeat_frequency
        self.repeat_interval = repeat_interval
        self.flexible_days = flexible_days
        self.show_blockings = show_blockings

        self.conflicts = 0
        self.bars = []

        if self.specific_room and self.rooms:
            raise ValueError('specific_room and rooms are mutually exclusive')

        if self.specific_room:
            self.rooms = [self.specific_room]
        elif self.rooms is None:
            self.rooms = Room.find_all(is_active=True)
        self.rooms = sorted(self.rooms, key=lambda x: natural_sort_key(x.full_name))

        if self.show_blockings:
            # avoid loading user data we don't care about
            user_strategy = defaultload('blocking').defaultload('created_by_user')
            user_strategy.noload('*')
            user_strategy.load_only('first_name', 'last_name')
            room_ids = [r.id for r in self.rooms]
            filters = {
                'room_ids': room_ids,
                'state': BlockedRoom.State.accepted,
                'start_date': self.start_dt.date(),
                'end_date': self.end_dt.date()
            }
            self.blocked_rooms = BlockedRoom.find_with_filters(filters).options(user_strategy)
            self.nonbookable_periods = NonBookablePeriod.find(
                NonBookablePeriod.room_id.in_(room_ids),
                NonBookablePeriod.overlaps(self.start_dt, self.end_dt)
            ).all()
        else:
            self.blocked_rooms = []

        self._produce_bars()

    def render(self, show_empty_rooms=True, show_empty_days=True, form_data=None, show_summary=True, show_navbar=True,
               can_navigate=True, details_in_new_tab=False):
        bars = self.build_bars_data(show_empty_rooms, show_empty_days)
        days = self.build_days_attrs() if self.specific_room and bars else {}

        period = self.end_dt.date() - self.start_dt.date() + timedelta(days=1)

        return WTemplated('RoomBookingCalendarWidget').getHTML({
            'form_data': form_data,
            'bars': bars,
            'days': days,
            'start_dt': self.start_dt,
            'end_dt': self.end_dt,
            'period_name': _('day') if period.days == 1 else _('period'),
            'specific_room': bool(self.specific_room),
            'show_summary': show_summary,
            'show_navbar': show_navbar,
            'can_navigate': show_navbar and can_navigate,
            'details_in_new_tab': details_in_new_tab,
            'repeat_frequency': self.repeat_frequency,
            'flexible_days': self.flexible_days
        })

    def iter_days(self):
        if self.repeat_frequency is None and self.repeat_interval is None:
            for dt in iterdays(self.start_dt, self.end_dt):
                yield dt.date()
        else:
            for dt in ReservationOccurrence.iter_start_time(self.start_dt, self.end_dt,
                                                            (self.repeat_frequency, self.repeat_interval)):
                for offset in xrange(-self.flexible_days, self.flexible_days + 1):
                    yield (dt + timedelta(days=offset)).date()

    def build_bars_data(self, show_empty_rooms=True, show_empty_days=True):
        bars_data = defaultdict(list)
        day_bars = group_list(self.bars, key=lambda b: b.date)

        for day in self.iter_days():
            bars = day_bars.get(day, [])
            if not bars and not show_empty_days:
                continue

            room_bars = group_list(bars, key=attrgetter('room_id'), sort_by=attrgetter('importance'))
            for room in self.rooms:
                bars = room_bars.get(room.id, [])
                if not bars and not show_empty_rooms:
                    continue
                room_dict = {
                    'room': room.to_serializable('__calendar_public__'),
                    'bars': [bar.to_serializable() for bar in bars]
                }
                bars_data[str(day)].append(room_dict)

        return bars_data

    def build_days_attrs(self):
        days_data = {}

        if self.specific_room and self.show_blockings:
            states = (BlockedRoom.State.accepted, BlockedRoom.State.pending)
            blocked_rooms = self.specific_room.get_blocked_rooms(*self.iter_days(), states=states)
        else:
            blocked_rooms = []

        for day in self.iter_days():
            attrs = {'tooltip': '', 'className': ''}

            # Lookup the blocking for the day
            for blocked_room in blocked_rooms:
                if blocked_room.blocking.is_active_at(day):
                    break
            else:
                blocked_room = None

            if blocked_room:
                blocking = blocked_room.blocking
                if blocking.can_be_overridden(session.user, explicit_only=True):
                    attrs['className'] = 'blocked_permitted'
                    attrs['tooltip'] = (_(u'Blocked by {0}:\n{1}\n\n'
                                          u'<strong>You are permitted to override the blocking.</strong>')
                                        .format(blocking.created_by_user.full_name, blocking.reason))
                elif blocked_room.state == BlockedRoom.State.accepted:
                    if blocking.can_be_overridden(session.user, room=self.specific_room):
                        attrs['className'] = 'blocked_override'
                        attrs['tooltip'] = _(
                            u'Blocked by {0}:\n{1}\n\n<b>You own this room or are an administrator '
                            u'and are thus permitted to override the blocking. Please use this '
                            u'privilege with care!</b>').format(blocking.created_by_user.full_name, blocking.reason)
                    else:
                        attrs['className'] = 'blocked'
                        attrs['tooltip'] = _(u'Blocked by {0}:\n{1}').format(blocking.created_by_user.full_name,
                                                                            blocking.reason)
                elif blocked_room.state == BlockedRoom.State.pending:
                    attrs['className'] = 'preblocked'
                    attrs['tooltip'] = _(
                        u'Blocking requested by {0}:\n{1}\n\n'
                        u'<b>If this blocking is approved, any colliding bookings will be rejected!</b>') \
                        .format(blocking.created_by_user.full_name, blocking.reason)
            days_data[str(day)] = attrs

        return days_data

    def _produce_bars(self):
        self._produce_reservation_bars()
        self._produce_prereservation_overlap_bars()
        if self.candidates is not None:
            self._produce_candidate_bars()
            self._produce_conflict_bars()
            self._produce_out_of_range_bars()
        if self.show_blockings:
            self._produce_blocking_bars()

    def _produce_reservation_bars(self):
        self.bars += map(Bar.from_occurrence, self.occurrences)

    def _produce_candidate_bars(self):
        blocked_rooms_by_room = MultiDict((br.room_id, br) for br in self.blocked_rooms)

        for room in self.rooms:
            blocked_rooms = blocked_rooms_by_room.getlist(room.id)
            for (start_dt, end_dt), candidates in self.candidates.iteritems():
                # Check if there's a blocking
                for blocked_room in blocked_rooms:
                    blocking = blocked_room.blocking
                    if overlaps((start_dt.date(), end_dt.date()), (blocking.start_date, blocking.end_date),
                                inclusive=True):
                        break
                else:
                    # In case we didn't break the loop due to a match
                    blocking = None
                for cand in candidates:
                    bar = Bar.from_candidate(cand, room.id, start_dt, end_dt, blocking)
                    self.bars.append(bar)

    def _produce_prereservation_overlap_bars(self):
        for _, occurrences in groupby((o for o in self.occurrences if not o.reservation.is_accepted),
                                      key=lambda o: o.reservation.room_id):
            occurrences = list(occurrences)
            for idx, o1 in enumerate(occurrences):
                for o2 in occurrences[idx+1:]:
                    if o1.overlaps(o2, skip_self=True):
                        start, end = o1.get_overlap(o2)
                        self.bars.append(Bar(start, end, overlapping=True, reservation=o2.reservation,
                                             kind=Bar.PRECONCURRENT))

    def _produce_conflict_bars(self):
        for candidates in self.candidates.itervalues():
            for candidate in candidates:
                for occurrence in self.occurrences:
                    if candidate.overlaps(occurrence, skip_self=True):
                        start, end = candidate.get_overlap(occurrence)
                        self.conflicts += occurrence.reservation.is_accepted
                        self.bars.append(Bar(start, end, overlapping=True, reservation=occurrence.reservation))

    def _produce_blocking_bars(self):
        for blocked_room in self.blocked_rooms:
            blocking = blocked_room.blocking
            self.bars.extend(Bar.from_blocked_room(blocked_room, day)
                             for day in self.iter_days()
                             if blocking.start_date <= day <= blocking.end_date)

        self.bars.extend(Bar.from_nonbookable_period(nbp, day)
                         for nbp in self.nonbookable_periods
                         for day in self.iter_days()
                         if nbp.start_dt.date() <= day <= nbp.end_dt.date())

    def _produce_out_of_range_bars(self):
        for room in self.rooms:
            self.bars.extend(
                Bar(datetime.combine(day, time()), datetime.combine(day, time(23, 59)), kind=Bar.OUT_OF_RANGE,
                    room_id=room.id)
                for day in self.iter_days()
                if not room.check_advance_days(day, user=session.user, quiet=True)
            )


class Bar(Serializer):
    __public__ = [
        'forReservation', 'blocking_data', 'startDT', 'endDT', ('kind', 'type'), ('reservation_start', 'resvStartDT'),
        ('reservation_end', 'resvEndDT')
    ]

    BLOCKED, PREBOOKED, PRECONCURRENT, UNAVAILABLE, CANDIDATE, PRECONFLICT, CONFLICT, OUT_OF_RANGE = range(8)
    _mapping = {
        BLOCKED: 'blocked',                 # A blocked-room period
        CANDIDATE: 'candidate',             # A reservation candidate
        CONFLICT: 'conflict',               # A conflicting reservation candidate
        PREBOOKED: 'pre-booked',            # A unconfirmed reservation
        PRECONCURRENT: 'pre-concurrent',    # A conflict between unconfirmed reservations
        PRECONFLICT: 'pre-conflict',        # A conflicting unconfirmed reservation
        UNAVAILABLE: 'unavailable',         # A confirmed reservation
        OUT_OF_RANGE: 'out_of_range'        # A period out of the booking range
    }

    def __init__(self, start, end, kind=None, reservation=None, overlapping=False, blocking=None, room_id=None,
                 nb_period=None):
        self.start = start
        self.end = end
        self.reservation = reservation
        self.reservation_start = None
        self.reservation_end = None
        self.room_id = room_id
        self.blocking = blocking
        self.nb_period = nb_period

        if reservation is not None:
            self.reservation_start = reservation.start_dt
            self.reservation_end = reservation.end_dt
            self.room_id = reservation.room_id
            if kind is None:
                if not overlapping:
                    kind = Bar.UNAVAILABLE if reservation.is_accepted else Bar.PREBOOKED
                else:
                    kind = Bar.CONFLICT if reservation.is_accepted else Bar.PRECONFLICT
        self.kind = kind

    def __cmp__(self, other):
        return cmp(self.kind, other.kind)

    def __repr__(self):
        return '<Bar({0}, {1}, {2}, {3}, {4})>'.format(
            self.start.date(),
            self.start.strftime('%H:%M'),
            self.end.strftime('%H:%M'),
            self.reservation.id if self.reservation else None,
            self._mapping[self.kind]
        )

    @classmethod
    def from_candidate(cls, candidate, room_id, resv_start, resv_end, blocking=None):
        self = cls(candidate.start_dt, candidate.end_dt, cls.CANDIDATE, blocking=blocking, room_id=room_id)
        self.reservation_start = resv_start
        self.reservation_end = resv_end
        return self

    @classmethod
    def from_occurrence(cls, occurrence):
        return cls(occurrence.start_dt, occurrence.end_dt, reservation=occurrence.reservation)

    @classmethod
    def from_blocked_room(cls, blocked_room, day):
        return cls(datetime.combine(day, time()), datetime.combine(day, time(23, 59)), Bar.BLOCKED,
                   blocking=blocked_room.blocking, room_id=blocked_room.room_id)

    @classmethod
    def from_nonbookable_period(cls, nb_period, day):
        return cls(datetime.combine(day, time()), datetime.combine(day, time(23, 59)), Bar.BLOCKED,
                   nb_period=nb_period, room_id=nb_period.room_id)

    @property
    def date(self):
        return self.start.date()

    @property
    def forReservation(self):
        if not self.reservation:
            return None
        return {
            'id': self.reservation.id,
            'bookedForName': self.reservation.booked_for_name,
            'reason': self.reservation.booking_reason,
            'bookingUrl': url_for('rooms.roomBooking-bookingDetails', self.reservation)
        }

    @property
    def blocking_data(self):
        if self.blocking:
            return {
                'id': self.blocking.id,
                'creator': self.blocking.created_by_user.full_name,
                'reason': self.blocking.reason,
                'blocking_url': url_for('rooms.blocking_details', blocking_id=self.blocking.id),
                'type': 'blocking'
            }
        elif self.nb_period:
            return {
                'id': None,
                'creator': None,
                'reason': 'Unavailable from {0} until {1}.'.format(format_date(self.nb_period.start_dt),
                                                                   format_date(self.nb_period.end_dt)),
                'blocking_url': None,
                'type': 'nonbookable'
            }
        return None

    @property
    def importance(self):
        return self.kind

    @property
    def startDT(self):
        return self.get_datetime('start')

    @property
    def endDT(self):
        return self.get_datetime('end')

    def get_datetime(self, attr):
        return {
            'date': str(self.start.date()),
            'tz': None,
            'time': getattr(self, attr).strftime('%H:%M')
        }
