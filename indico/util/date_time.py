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

from collections import OrderedDict
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
from dateutil.relativedelta import relativedelta as _relativedelta

from indico.core.config import Config
from indico.legacy.common.timezoneUtils import DisplayTZ
from indico.util.i18n import get_current_locale, _, ngettext, parse_locale
from indico.util.string import inject_unicode_debug


class relativedelta(_relativedelta):
    """Improved `relativedelta`"""

    def __abs__(self):
        return self.__class__(years=abs(self.years),
                              months=abs(self.months),
                              days=abs(self.days),
                              hours=abs(self.hours),
                              minutes=abs(self.minutes),
                              seconds=abs(self.seconds),
                              microseconds=abs(self.microseconds),
                              leapdays=self.leapdays,
                              year=self.year,
                              month=self.month,
                              day=self.day,
                              weekday=self.weekday,
                              hour=self.hour,
                              minute=self.minute,
                              second=self.second,
                              microsecond=self.microsecond)


def now_utc(exact=True):
    """Get the current date/time in UTC

    :param exact: Set to ``False`` to set seconds/microseconds to 0.
    :return: A timezone-aware `datetime` object
    """
    now = datetime.utcnow()
    if not exact:
        now = now.replace(second=0, microsecond=0)
    return pytz.utc.localize(now)


def as_utc(dt):
    """Returns the given naive datetime with tzinfo=UTC."""
    if dt.tzinfo and dt.tzinfo != pytz.utc:
        raise ValueError("{} already contains non-UTC tzinfo data".format(dt))
    return pytz.utc.localize(dt) if dt.tzinfo is None else dt


def localize_as_utc(dt, timezone='UTC'):
    """Localizes a naive datetime with the timezone and returns it as UTC.

    :param dt: A naive :class:`datetime.datetime` object.
    :param timezone: The timezone from which to localize.  UTC by default.
    """
    timezone = pytz.timezone(timezone)
    return timezone.localize(dt).astimezone(pytz.utc)


def server_to_utc(dt):
    """Converts the given datetime in the server's TZ to UTC.

    The given datetime **MUST** be naive but already contain the correct time in the server's TZ.
    """
    server_tz = get_timezone(Config.getInstance().getDefaultTimezone())
    return server_tz.localize(dt).astimezone(pytz.utc)


def utc_to_server(dt):
    """Converts the given UTC datetime to the server's TZ."""
    server_tz = get_timezone(Config.getInstance().getDefaultTimezone())
    return dt.astimezone(server_tz)


def format_datetime(dt, format='medium', locale=None, timezone=None, server_tz=False, keep_tz=False):
    """
    Basically a wrapper around Babel's own format_datetime
    """
    inject_unicode = True
    if format == 'code':
        format = 'dd/MM/yyyy HH:mm'
        inject_unicode = False
    if not locale:
        locale = get_current_locale()
    if keep_tz:
        assert timezone is None
        timezone = dt.tzinfo
    elif not timezone and dt.tzinfo:
        timezone = DisplayTZ().getDisplayTZ()
    elif server_tz:
        timezone = Config.getInstance().getDefaultTimezone()

    rv = _format_datetime(dt, format=format, locale=locale, tzinfo=timezone)
    return inject_unicode_debug(rv, 2).encode('utf-8') if inject_unicode else rv.encode('utf-8')


def format_date(d, format='medium', locale=None, timezone=None):
    """
    Basically a wrapper around Babel's own format_date
    """
    inject_unicode = True
    if format == 'code':
        format = 'dd/MM/yyyy'
        inject_unicode = False
    if not locale:
        locale = get_current_locale()
    if timezone and isinstance(d, datetime) and d.tzinfo:
        d = d.astimezone(pytz.timezone(timezone) if isinstance(timezone, basestring) else timezone)

    rv = _format_date(d, format=format, locale=locale)
    return inject_unicode_debug(rv, 2).encode('utf-8') if inject_unicode else rv.encode('utf-8')


def format_time(t, format='short', locale=None, timezone=None, server_tz=False):
    """
    Basically a wrapper around Babel's own format_time
    """
    inject_unicode = True
    if format == 'code':
        format = 'HH:mm'
        inject_unicode = False
    if not locale:
        locale = get_current_locale()
    if not timezone and t.tzinfo:
        timezone = DisplayTZ().getDisplayTZ()
    elif server_tz:
        timezone = Config.getInstance().getDefaultTimezone()
    if timezone:
        timezone = get_timezone(timezone)

    rv = _format_time(t, format=format, locale=locale, tzinfo=timezone)
    return inject_unicode_debug(rv, 2).encode('utf-8') if inject_unicode else rv.encode('utf-8')


def format_timedelta(td, format='short', threshold=0.85, locale=None):
    """
    Basically a wrapper around Babel's own format_timedelta
    """
    if not locale:
        locale = get_current_locale()

    rv = _format_timedelta(td, format=format, locale=locale, threshold=threshold)
    return inject_unicode_debug(rv, 2).encode('utf-8')


def format_human_timedelta(delta, granularity='seconds', narrow=False):
    """Formats a timedelta in a human-readable way

    :param delta: the timedelta to format
    :param granularity: the granularity, i.e. the lowest unit that is
                        still displayed. when set e.g. to 'minutes',
                        the output will never contain seconds unless
                        the whole timedelta spans less than a minute.
                        Accepted values are 'seconds', 'minutes',
                        'hours' and 'days'.
    :param narrow: if true, only the short unit names will be used
    """
    field_order = ('days', 'hours', 'minutes', 'seconds')
    long_names = {
        'seconds': lambda n: ngettext(u'{0} second', u'{0} seconds', n).format(n),
        'minutes': lambda n: ngettext(u'{0} minute', u'{0} minutes', n).format(n),
        'hours': lambda n: ngettext(u'{0} hour', u'{0} hours', n).format(n),
        'days': lambda n: ngettext(u'{0} day', u'{0} days', n).format(n),
    }
    short_names = {
        'seconds': lambda n: ngettext(u'{0}s', u'{0}s', n).format(n),
        'minutes': lambda n: ngettext(u'{0}m', u'{0}m', n).format(n),
        'hours': lambda n: ngettext(u'{0}h', u'{0}h', n).format(n),
        'days': lambda n: ngettext(u'{0}d', u'{0}d', n).format(n),
    }
    if narrow:
        long_names = short_names
    values = OrderedDict((key, 0) for key in field_order)
    values['seconds'] = delta.total_seconds()
    values['days'], values['seconds'] = divmod(values['seconds'], 86400)
    values['hours'], values['seconds'] = divmod(values['seconds'], 3600)
    values['minutes'], values['seconds'] = divmod(values['seconds'], 60)
    for key, value in values.iteritems():
        values[key] = int(value)
    # keep all fields covered by the granularity, and if that results in
    # no non-zero fields, include otherwise excluded ones
    used_fields = set(field_order[:field_order.index(granularity) + 1])
    available_fields = [x for x in field_order if x not in used_fields]
    used_fields -= {k for k, v in values.iteritems() if not v}
    while not sum(values[x] for x in used_fields) and available_fields:
        used_fields.add(available_fields.pop(0))
    for key in available_fields:
        values[key] = 0
    nonzero = OrderedDict((k, v) for k, v in values.iteritems() if v)
    if not nonzero:
        return long_names[granularity](0)
    elif len(nonzero) == 1:
        key, value = nonzero.items()[0]
        return long_names[key](value)
    else:
        parts = [short_names[key](value) for key, value in nonzero.iteritems()]
        return u' '.join(parts)


def format_human_date(dt, format='medium', locale=None):
    """
    Return the date in a human-like format for yesterday, today and tomorrow.
    Format the date otherwise.
    """
    today = now_utc().date()
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


def _format_pretty_datetime(dt, locale, tzinfo, formats):
    locale = get_current_locale() if not locale else parse_locale(locale)

    if tzinfo:
        if dt.tzinfo:
            dt = dt.astimezone(tzinfo)
        else:
            dt = tzinfo.localize(dt).astimezone(tzinfo)

    today = (now_utc(False).astimezone(tzinfo) if tzinfo else now_utc(False)).replace(hour=0, minute=0)
    diff = (dt - today).total_seconds() / 86400.0
    mapping = [(-6, 'other'), (-1, 'last_week'), (0, 'last_day'),
               (1, 'same_day'), (2, 'next_day'), (7, 'next_week'),
               (None, 'other')]

    fmt = next(formats[key] for delta, key in mapping if delta is None or diff < delta)
    fmt = fmt.format(date_fmt=locale.date_formats['medium'], time_fmt=locale.time_formats['short'])
    return _format_datetime(dt, fmt, tzinfo, locale)


def format_pretty_date(dt, locale=None, tzinfo=None):
    """Format a date in a pretty way using relative units if possible.

    :param dt: a date or datetime object. if a date is provided, its
               time is assumed to be midnight
    :param locale: the locale to use for formatting
    :param tzinfo: the timezone to use
    """
    if not isinstance(dt, datetime):
        dt = datetime.combine(dt, dt_time())
    return _format_pretty_datetime(dt, locale, tzinfo, {
        'last_day': _(u"'Yesterday'"),
        'same_day': _(u"'Today'"),
        'next_day': _(u"'Tomorrow'"),
        'last_week': _(u"'Last' EEEE"),
        'next_week': _(u"EEEE"),
        'other': _(u"{date_fmt}")
    })


def format_pretty_datetime(dt, locale=None, tzinfo=None):
    """
    Format a datetime in a pretty way using relative units for the
    date if possible.

    :param dt: a datetime object
    :param locale: the locale to use for formatting
    :param tzinfo: the timezone to use
    """

    return _format_pretty_datetime(dt, locale, tzinfo, {
        'last_day': _(u"'Yesterday' 'at' {time_fmt}"),
        'same_day': _(u"'Today' 'at' {time_fmt}"),
        'next_day': _(u"'Tomorrow' 'at' {time_fmt}"),
        'last_week': _(u"'Last' EEEE 'at' {time_fmt}"),
        'next_week': _(u"EEEE 'at' {time_fmt}"),
        'other': _(u"{date_fmt} 'at' {time_fmt}")
    })


def format_number(number, locale=None):
    if not locale:
        locale = get_current_locale()
    rv = _format_number(number, locale=locale)
    return inject_unicode_debug(rv, 2).encode('utf-8')


def timedelta_split(delta):
    """
    Decomposes a timedelta into hours, minutes and seconds
    (timedelta only stores days and seconds)n
    """
    sec = delta.seconds + delta.days * 24 * 3600
    hours, remainder = divmod(sec, 3600)
    minutes, seconds = divmod(remainder, 60)
    return hours, minutes, seconds


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


def iterdays(start, end, skip_weekends=False, day_whitelist=None, day_blacklist=None):
    weekdays = (MO, TU, WE, TH, FR) if skip_weekends else None
    start = get_day_start(start) if isinstance(start, datetime) else start
    end = get_day_end(end) if isinstance(end, datetime) else end
    for day in rrule(DAILY, dtstart=start, until=end, byweekday=weekdays):
        if day_whitelist and day.date() not in day_whitelist:
            continue
        if day_blacklist and day.date() in day_blacklist:
            continue
        yield day


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


def get_day_start(day, tzinfo=None):
    """Return the earliest datetime for a given day.

    :param day: A `date` or `datetime`.
    :param tzinfo: The timezone to display the resulting datetime. Not valid for
                   non-naive `datetime` objects.
    """
    if isinstance(day, datetime):
        if day.tzinfo and tzinfo:
            raise ValueError("datetime is not naive.")
        tzinfo = day.tzinfo
        day = day.date()
    start_dt = datetime.combine(day, dt_time(0))
    return tzinfo.localize(start_dt) if tzinfo else start_dt


def get_day_end(day, tzinfo=None):
    """Return the latest datetime for a given day.

    :param day: A `date` or `datetime`.
    :param tzinfo: The timezone to display the resulting datetime. Not valid for
                   non-naive `datetime` objects.
    """
    if isinstance(day, datetime):
        if day.tzinfo and tzinfo:
            raise ValueError("datetime is not naive.")
        tzinfo = day.tzinfo
        day = day.date()
    end_dt = datetime.combine(day, dt_time(23, 59))
    return tzinfo.localize(end_dt) if tzinfo else end_dt


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


def strftime_all_years(dt, fmt):
    """Exactly like datetime.strftime but supports year<1900"""
    assert '%%Y' not in fmt  # unlikely but just in case
    if dt.year >= 1900:
        return dt.strftime(fmt)
    else:
        return dt.replace(year=1900).strftime(fmt.replace('%Y', '%%Y')).replace('%Y', unicode(dt.year))
