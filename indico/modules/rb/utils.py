# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from datetime import date, datetime, timedelta

from indico.util.caching import memoize_request
from indico.util.date_time import get_day_end, round_up_to_minutes
from indico.modules.rb.models.locations import Location
from indico.util.user import retrieve_principals, principals_merge_users


@memoize_request
def rb_check_user_access(user):
    """Checks if the user has access to the room booking system"""
    from indico.modules.rb import settings as rb_settings

    if user.isRBAdmin():
        return True
    principals = retrieve_principals(rb_settings.get('authorized_principals'))
    if not principals:  # everyone has access
        return True
    return any(principal.containsUser(user) for principal in principals)


def rb_merge_users(new_id, old_id):
    """Updates RB data after an Avatar merge

    :param new_id: Target user
    :param old_id: Source user (being deleted in the merge)
    """
    from indico.modules.rb import settings as rb_settings
    from indico.modules.rb.models.blocking_principals import BlockingPrincipal
    from indico.modules.rb.models.blockings import Blocking
    from indico.modules.rb.models.reservations import Reservation
    from indico.modules.rb.models.rooms import Room

    BlockingPrincipal.find(entity_type='Avatar', entity_id=old_id).update({'entity_id': new_id})
    Blocking.find(created_by_id=old_id).update({'created_by_id': new_id})
    Reservation.find(created_by_id=old_id).update({'created_by_id': new_id})
    Reservation.find(booked_for_id=old_id).update({'booked_for_id': new_id})
    Room.find(owner_id=old_id).update({'owner_id': new_id})
    for key in ('authorized_principals', 'admin_principals'):
        principals = rb_settings.get(key)
        principals = principals_merge_users(principals, new_id, old_id)
        rb_settings.set(key, principals)


def get_default_booking_interval(duration=90, precision=15, force_today=False):
    """Get the default booking interval for a room.

    Returns the default booking interval for a room as a tuple containing
    the start and end times as `datetime` objects.

    The start time is the default working start time or the current time (if the
    working start time is in the past); rounded up to the given precision in
    minutes (15 by default).

    The end time corresponds to the start time plus the given duration in
    minutes. If the booking is ends after the end of work time, it is
    automatically moved to the next day.

    :param duration: int -- The duration of a booking in minutes (must be
        greater than 1)
    :param precision: int -- The number of minutes by which to round up the
        current time for the start time of a booking. Negative values are
        allowed but will round the time down and create a booking starting in
        the past.
    :param force_today: Forces a booking to be for today, even if it past the
        end of work time. This is ignored if the current time is either after
        23:50 or within the amount of minutes of the precision from midnight.
        For example with a precision of 30 minutes, if the current time is 23:42
        then the meeting will be the following day.
    :returns: (datetime, datetime, bool) -- A tuple with the start and end times
        of the booking and a boolean which is `True` if the date was changed
        from today and `False` otherwise.
    :raises: ValueError if the duration is less than 1 minute
    """
    if duration < 1:
        raise ValueError("The duration must be strictly positive (got {} min)".format(duration))

    date_changed = False
    work_start = datetime.combine(date.today(), Location.working_time_start)
    work_end = datetime.combine(date.today(), Location.working_time_end)
    start_dt = max(work_start, round_up_to_minutes(datetime.now(), precision=precision))

    end_dt = start_dt + timedelta(minutes=duration)
    if end_dt.date() > start_dt.date():
        end_dt = get_day_end(start_dt.date())

    if ((not force_today and start_dt > work_end) or
            start_dt.date() > date.today() or
            end_dt - start_dt < timedelta(minutes=10)):
        date_changed = True
        start_dt = work_start + timedelta(days=1)
        end_dt = start_dt + timedelta(minutes=duration)
    return start_dt, end_dt, date_changed
