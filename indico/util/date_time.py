# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

import re
from collections import Counter
from datetime import datetime
from datetime import time as dt_time
from datetime import timedelta

import pytz
from babel.dates import format_date as _format_date
from babel.dates import format_datetime as _format_datetime
from babel.dates import format_interval as _format_interval
from babel.dates import format_time as _format_time
from babel.dates import format_timedelta as _format_timedelta
from babel.dates import get_timezone, match_skeleton
from babel.numbers import format_number as _format_number
from dateutil.relativedelta import relativedelta as _relativedelta
from dateutil.rrule import DAILY, FR, MO, TH, TU, WE, rrule
from flask import has_request_context, session

from indico.core.config import config
from indico.util.i18n import IndicoLocale, _, get_current_locale, ngettext, parse_locale


class relativedelta(_relativedelta):
    """Improved `relativedelta`."""

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
    """Get the current date/time in UTC.

    :param exact: Set to ``False`` to set seconds/microseconds to 0.
    :return: A timezone-aware `datetime` object
    """
    now = datetime.utcnow()
    if not exact:
        now = now.replace(second=0, microsecond=0)
    return pytz.utc.localize(now)


def as_utc(dt):
    """Return the given naive datetime with tzinfo=UTC."""
    if dt.tzinfo and dt.tzinfo != pytz.utc:
        raise ValueError(f'{dt} already contains non-UTC tzinfo data')
    return pytz.utc.localize(dt) if dt.tzinfo is None else dt


def localize_as_utc(dt, timezone='UTC'):
    """Localize a naive datetime with the timezone and returns it as UTC.

    :param dt: A naive :class:`datetime.datetime` object.
    :param timezone: The timezone from which to localize.  UTC by default.
    """
    timezone = pytz.timezone(timezone)
    return timezone.localize(dt).astimezone(pytz.utc)


def server_to_utc(dt):
    """Convert the given datetime in the server's TZ to UTC.

    The given datetime **MUST** be naive but already contain the
    correct time in the server's TZ.
    """
    server_tz = get_timezone(config.DEFAULT_TIMEZONE)
    return server_tz.localize(dt).astimezone(pytz.utc)


def utc_to_server(dt):
    """Convert the given UTC datetime to the server's TZ."""
    server_tz = get_timezone(config.DEFAULT_TIMEZONE)
    return dt.astimezone(server_tz)


def format_datetime(dt, format='medium', locale=None, timezone=None):
    """Basically a wrapper around Babel's own format_datetime."""
    if format == 'code':
        format = 'dd/MM/yyyy HH:mm'
    if not locale:
        locale = get_current_locale()
    if not timezone and dt.tzinfo:
        timezone = session.tzinfo

    return _format_datetime(dt, format=format, locale=locale, tzinfo=timezone)


def format_date(d, format='medium', locale=None, timezone=None):
    """Basically a wrapper around Babel's own format_date."""
    if format == 'code':
        format = 'dd/MM/yyyy'
    if not locale:
        locale = get_current_locale()
    if timezone and isinstance(d, datetime) and d.tzinfo:
        d = d.astimezone(pytz.timezone(timezone) if isinstance(timezone, str) else timezone)

    return _format_date(d, format=format, locale=locale)


def format_time(t, format='short', locale=None, timezone=None, server_tz=False):
    """Basically a wrapper around Babel's own format_time."""
    if format == 'code':
        format = 'HH:mm'
    if not locale:
        locale = get_current_locale()
    if not timezone and t.tzinfo:
        timezone = session.tzinfo
    elif server_tz:
        timezone = config.DEFAULT_TIMEZONE
    if isinstance(timezone, str):
        timezone = get_timezone(timezone)
    return _format_time(t, format=format, locale=locale, tzinfo=timezone)


def format_timedelta(td, format='short', threshold=0.85, locale=None):
    """Basically a wrapper around Babel's own format_timedelta."""
    if not locale:
        locale = get_current_locale()

    return _format_timedelta(td, format=format, locale=locale, threshold=threshold)


def format_interval(start_dt, end_dt, format='yMd', locale=None):
    """Basically a wrapper around Babel's own format_interval."""
    if not locale:
        locale = get_current_locale()

    return _format_interval(start_dt, end_dt, format, locale=locale)


def _adjust_skeleton(format, skeleton):
    for char, count in Counter(skeleton).items():
        format = re.sub(fr'{re.escape(char)}+', char * count, format)
    return format


def format_skeleton(dt, skeleton, locale=None, timezone=None):
    """Basically a wrapper around Babel's own format_skeleton.

    It also keeps the specified width from the originally requested
    skeleton string and adjusts the one from the locale data accordingly.

    The argument order is swapped to keep uniformity with other format_* functions.
    """
    if not locale:
        locale = get_current_locale()
    if not timezone and isinstance(dt, datetime) and dt.tzinfo:
        timezone = session.tzinfo

    # See https://github.com/python-babel/babel/issues/803 if you wonder why
    # we aren't using the default format_skeleton from Babel.
    locale = IndicoLocale.parse(locale)
    requested_skeleton = skeleton
    if skeleton not in locale.datetime_skeletons:
        skeleton = match_skeleton(skeleton, locale.datetime_skeletons)
    format = locale.datetime_skeletons[skeleton]
    format = _adjust_skeleton(str(format), requested_skeleton)
    return _format_datetime(dt, format=format, locale=locale, tzinfo=timezone)


def format_human_timedelta(delta, granularity='seconds', narrow=False):
    """Format a timedelta in a human-readable way.

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
        'seconds': lambda n: ngettext('{0} second', '{0} seconds', n).format(n),
        'minutes': lambda n: ngettext('{0} minute', '{0} minutes', n).format(n),
        'hours': lambda n: ngettext('{0} hour', '{0} hours', n).format(n),
        'days': lambda n: ngettext('{0} day', '{0} days', n).format(n),
    }
    short_names = {
        'seconds': lambda n: ngettext('{0}s', '{0}s', n).format(n),
        'minutes': lambda n: ngettext('{0}m', '{0}m', n).format(n),
        'hours': lambda n: ngettext('{0}h', '{0}h', n).format(n),
        'days': lambda n: ngettext('{0}d', '{0}d', n).format(n),
    }
    if narrow:
        long_names = short_names
    values = {key: 0 for key in field_order}
    values['seconds'] = delta.total_seconds()
    values['days'], values['seconds'] = divmod(values['seconds'], 86400)
    values['hours'], values['seconds'] = divmod(values['seconds'], 3600)
    values['minutes'], values['seconds'] = divmod(values['seconds'], 60)
    for key, value in values.items():
        values[key] = int(value)
    # keep all fields covered by the granularity, and if that results in
    # no non-zero fields, include otherwise excluded ones
    used_fields = set(field_order[:field_order.index(granularity) + 1])
    available_fields = [x for x in field_order if x not in used_fields]
    used_fields -= {k for k, v in values.items() if not v}
    while not sum(values[x] for x in used_fields) and available_fields:
        used_fields.add(available_fields.pop(0))
    for key in available_fields:
        values[key] = 0
    nonzero = {k: v for k, v in values.items() if v}
    if not nonzero:
        return long_names[granularity](0)
    elif len(nonzero) == 1:
        key, value = list(nonzero.items())[0]
        return long_names[key](value)
    else:
        parts = [short_names[key](value) for key, value in nonzero.items()]
        return ' '.join(parts)


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
        return _('yesterday')
    elif dt == today:
        return _('today')
    elif dt == today + oneday:
        return _('tomorrow')
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
        'last_day': _("'Yesterday'"),
        'same_day': _("'Today'"),
        'next_day': _("'Tomorrow'"),
        'last_week': _("'Last' EEEE"),
        'next_week': _('EEEE'),
        'other': '{date_fmt}'
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
        'last_day': _("'Yesterday' 'at' {time_fmt}"),
        'same_day': _("'Today' 'at' {time_fmt}"),
        'next_day': _("'Tomorrow' 'at' {time_fmt}"),
        'last_week': _("'Last' EEEE 'at' {time_fmt}"),
        'next_week': _("EEEE 'at' {time_fmt}"),
        'other': _("{date_fmt} 'at' {time_fmt}")
    })


def format_number(number, locale=None):
    if not locale:
        locale = get_current_locale()
    return _format_number(number, locale=locale)


def timedelta_split(delta):
    """
    Decompose a timedelta into hours, minutes and seconds
    (timedelta only stores days and seconds).
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
    tzinfo = start.tzinfo if isinstance(start, datetime) else None
    weekdays = (MO, TU, WE, TH, FR) if skip_weekends else None
    start = get_day_start(start).replace(tzinfo=None) if isinstance(start, datetime) else start
    end = get_day_end(end).replace(tzinfo=None) if isinstance(end, datetime) else end
    for day in rrule(DAILY, dtstart=start, until=end, byweekday=weekdays):
        if tzinfo:
            day = tzinfo.localize(day)
        if day_whitelist and day.date() not in day_whitelist:
            continue
        if day_blacklist and day.date() in day_blacklist:
            continue
        yield day


def get_day_start(day, tzinfo=None):
    """Return the earliest datetime for a given day.

    :param day: A `date` or `datetime`.
    :param tzinfo: The timezone to display the resulting datetime. Not valid for
                   non-naive `datetime` objects.
    """
    if isinstance(day, datetime):
        if day.tzinfo and tzinfo:
            raise ValueError('datetime is not naive.')
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
            raise ValueError('datetime is not naive.')
        tzinfo = day.tzinfo
        day = day.date()
    end_dt = datetime.combine(day, dt_time(23, 59))
    return tzinfo.localize(end_dt) if tzinfo else end_dt


def strftime_all_years(dt, fmt):
    """Exactly like datetime.strftime but supports year<1900."""
    assert '%%Y' not in fmt  # unlikely but just in case
    if dt.year >= 1900:
        return dt.strftime(fmt)
    else:
        return dt.replace(year=1900).strftime(fmt.replace('%Y', '%%Y')).replace('%Y', str(dt.year))


def get_display_tz(obj=None, as_timezone=False):
    display_tz = session.timezone if has_request_context() else 'LOCAL'
    if display_tz == 'LOCAL':
        if obj is None:
            display_tz = config.DEFAULT_TIMEZONE
        else:
            display_tz = getattr(obj, 'timezone', 'UTC')
    if not display_tz:
        display_tz = config.DEFAULT_TIMEZONE
    return pytz.timezone(display_tz) if as_timezone else display_tz
