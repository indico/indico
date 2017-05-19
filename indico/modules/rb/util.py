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

from datetime import date, datetime, timedelta

from indico.modules.rb.models.locations import Location
from indico.util.caching import memoize_request
from indico.util.date_time import get_day_end, round_up_to_minutes
from indico.util.user import unify_user_args


@unify_user_args
@memoize_request
def rb_check_user_access(user):
    """Checks if the user has access to the room booking system"""
    from indico.modules.rb import rb_settings
    if rb_is_admin(user):
        return True
    if not rb_settings.acls.get('authorized_principals'):  # everyone has access
        return True
    return rb_settings.acls.contains_user('authorized_principals', user)


@unify_user_args
def rb_is_admin(user):
    """Checks if the user is a room booking admin"""
    from indico.modules.rb import rb_settings
    if user.is_admin:
        return True
    return rb_settings.acls.contains_user('admin_principals', user)


def get_default_booking_interval(duration=90, precision=15, force_today=False):
    """Get the default booking interval for a room.

    Returns the default booking interval for a room as a tuple containing
    the start and end times as `datetime` objects.

    The start time is the default working start time or the current time (if the
    working start time is in the past); rounded up to the given precision in
    minutes (15 by default).

    The end time corresponds to the start time plus the given duration in
    minutes. If the booking ends after the end of work time, it is
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
    work_start = datetime.combine(date.today(), Location.working_time_periods[0][0])
    work_end = datetime.combine(date.today(), Location.working_time_periods[-1][1])
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
