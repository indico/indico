# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico;if not, see <http://www.gnu.org/licenses/>.

import calendar
import time
from datetime import timedelta, datetime
from datetime import time as dt_time

import pytz
from flask import request
from babel.dates import format_datetime as _format_datetime
from babel.dates import format_time as _format_time
from babel.dates import format_date as _format_date
from babel.dates import format_timedelta as _format_timedelta
from babel.dates import get_timezone
from babel.numbers import format_number as _format_number
from dateutil.rrule import rrule, DAILY, MO, TU, WE, TH, FR, SA, SU
from dateutil.relativedelta import relativedelta

from MaKaC.common import HelperMaKaCInfo
from MaKaC.common.timezoneUtils import nowutc, DisplayTZ
from indico.util.i18n import get_current_locale


now_utc = nowutc


def utc_timestamp(datetimeVal):
    return int(calendar.timegm(datetimeVal.utctimetuple()))


def as_utc(dt):
    """Returns the given datetime with tzinfo=UTC.

    The given datetime object **MUST** be naive but already contain UTC!
    """
    return pytz.utc.localize(dt)


def server_to_utc(dt):
    """Converts the given datetime in the server's TZ to UTC.

    The given datetime **MUST** be naive but already contain the correct time in the server's TZ.
    """
    server_tz = get_timezone(HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone())
    return server_tz.localize(dt).astimezone(pytz.utc)


def utc_to_server(dt):
    """Converts the given UTC datetime to the server's TZ."""
    server_tz = get_timezone(HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone())
    return dt.astimezone(server_tz)


def format_datetime(dt, format='medium', locale=None, timezone=None, server_tz=False, keep_tz=False):
    """
    Basically a wrapper around Babel's own format_datetime
    """
    if not locale:
        locale = get_current_locale()
    if keep_tz:
        assert timezone is None
        timezone = dt.tzinfo
    elif not timezone and dt.tzinfo:
        timezone = DisplayTZ().getDisplayTZ()
    elif server_tz:
        timezone = HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()

    return _format_datetime(dt, format=format, locale=locale, tzinfo=timezone).encode('utf-8')


def format_date(d, format='medium', locale=None):
    """
    Basically a wrapper around Babel's own format_date
    """
    if not locale:
        locale = get_current_locale()

    return _format_date(d, format=format, locale=locale).encode('utf-8')


def format_time(t, format='short', locale=None, timezone=None, server_tz=False):
    """
    Basically a wrapper around Babel's own format_time
    """
    if not locale:
        locale = get_current_locale()
    if not timezone and t.tzinfo:
        timezone = DisplayTZ().getDisplayTZ()
    elif server_tz:
        timezone = HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()
    if timezone:
        timezone = get_timezone(timezone)

    return _format_time(t, format=format, locale=locale, tzinfo=timezone).encode('utf-8')


def format_timedelta(td, format='short', locale=None):
    """
    Basically a wrapper around Babel's own format_timedelta
    """
    if not locale:
        locale = get_current_locale()

    return _format_timedelta(td, format=format, locale=locale).encode('utf-8')


def format_human_date(dt, format='medium', locale=None):
    """
    Return the date in a human-like format for yesterday, today and tomorrow.
    Format the date otherwise.
    """
    today = nowutc().date()
    oneday = timedelta(days=1)

    if not locale:
        locale = get_current_locale()

    if dt == today - oneday:
        return _("yesterday")
    elif dt == today:
        return _("today")
    elif dt == today + oneday:
        return _("tomorrow")
    else:
        return format_date(dt, format, locale=locale)


def format_number(number, locale=None):
    if not locale:
        locale = get_current_locale()
    return _format_number(number, locale=locale).encode('utf-8')


def is_same_month(date_1, date_2):
    """
    This method ensures that is the same month of the same year
    """
    return date_1.month == date_2.month and date_1.year == date_2.year


def timedelta_split(delta):
    """
    Decomposes a timedelta into hours, minutes and seconds
    (timedelta only stores days and seconds)n
    """
    sec = delta.seconds + delta.days * 24 * 3600
    hours, remainder = divmod(sec, 3600)
    minutes, seconds = divmod(remainder, 60)
    return hours, minutes, seconds


## ATTENTION: Do not use this one for new developments ##
# It is flawed, as even though the returned value is DST-safe,
# it is in the _local timezone_, meaning that the number of seconds
# returned is the one for the hour with the same "value" for the
# local timezone.
def int_timestamp(datetimeVal, tz=pytz.timezone('UTC')):
    """
    Returns the number of seconds from the local epoch to the UTC time
    """
    return int(time.mktime(datetimeVal.astimezone(tz).timetuple()))


def overlaps(range1, range2, inclusive=False):
    start1, end1 = range1
    start2, end2 = range2

    if inclusive:
        return start1 <= end2 and start2 <= end1
    else:
        return start1 < end2 and start2 < end1


def get_overlap(range1, range2):
    if not overlaps(range1, range2):
        return None, None

    start1, end1 = range1
    start2, end2 = range2

    latest_start = max(start1, start2)
    earliest_end = min(end1, end2)

    return latest_start, earliest_end


def iterdays(start, end, skip_weekends=False):
    weekdays = (MO, TU, WE, TH, FR) if skip_weekends else None
    start = get_day_start(start) if isinstance(start, datetime) else start
    end = get_day_end(end) if isinstance(end, datetime) else end
    return rrule(DAILY, dtstart=start, until=end, byweekday=weekdays)


def is_weekend(d):
    return d.weekday() in [e.weekday for e in (SA, SU)]


def get_datetime_from_request(prefix='', default=None, source=None):
    """Retrieves date and time from request data."""
    if source is None:
        source = request.values

    if default is None:
        default = datetime.now()

    date_str = source.get('{}date'.format(prefix), '')
    time_str = source.get('{}time'.format(prefix), '')

    try:
        parsed_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        parsed_date = default.date()

    try:
        parsed_time = datetime.strptime(time_str, '%H:%M').time()
    except ValueError:
        parsed_time = default.time()

    return datetime.combine(parsed_date, parsed_time)


def get_day_start(day):
    tzinfo = None
    if isinstance(day, datetime):
        tzinfo = day.tzinfo
        day = day.date()
    return datetime.combine(day, dt_time(0, tzinfo=tzinfo))


def get_day_end(day):
    tzinfo = None
    if isinstance(day, datetime):
        tzinfo = day.tzinfo
        day = day.date()
    return datetime.combine(day, dt_time(23, 59, tzinfo=tzinfo))


def round_up_to_minutes(dt, precision=15):
    """
    Rounds up a date time object to the given precision in minutes.

    :param dt: datetime -- the time to round up
    :param precision: int -- the precision to round up by in minutes. Negative
        values for the precision are allowed but will round down instead of up.
    :returns: datetime -- the time rounded up by the given precision in minutes.
    """
    increment = precision * 60
    secs_in_current_hour = (dt.minute * 60) + dt.second + (dt.microsecond * 1e-6)
    delta = (secs_in_current_hour // increment) * increment + increment - secs_in_current_hour
    return dt + timedelta(seconds=delta)


def get_month_start(date):
    return date + relativedelta(day=1)


def get_month_end(date):
    return date + relativedelta(day=1, months=+1, days=-1)


def round_up_month(date, from_day=1):
    """Rounds up a date to the next month unless its day is before *from_day*.

    :param date: date object
    :param from_day: day from which one to round *date* up
    """
    if date.day >= from_day:
        return date + relativedelta(day=1, months=+1)
    else:
        return date
