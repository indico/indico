# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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

import time, pytz, calendar

from MaKaC.common.timezoneUtils import nowutc
from indico.util.i18n import currentLocale
from babel.dates import format_datetime as _format_datetime
from babel.dates import format_time as _format_time
from babel.dates import format_date as _format_date
from babel.numbers import format_number as _format_number


def utc_timestamp(datetimeVal):
    return int(calendar.timegm(datetimeVal.utctimetuple()))


def format_datetime(dt, format='medium', locale=None, timezone=None):
    """
    Basically a wrapper around Babel's own format_datetime
    """
    if not locale:
        locale = currentLocale()

    return _format_datetime(dt, format=format, locale=locale, tzinfo=timezone).encode('utf-8')

def format_date(d, format='medium', locale=None):
    """
    Basically a wrapper around Babel's own format_date
    """
    if not locale:
        locale = currentLocale()

    return _format_date(d, format=format, locale=locale).encode('utf-8')

def format_time(t, format='short', locale=None, timezone=None):
    """
    Basically a wrapper around Babel's own format_time
    """
    if not locale:
        locale = currentLocale()

    return _format_time(t, format=format, locale=locale, tzinfo=timezone).encode('utf-8')

now_utc = nowutc

def format_number(number, locale=None):
    if not locale:
        locale = currentLocale()
    return _format_number(number, locale=locale).encode('utf-8')

def is_same_month(date_1, date_2):
    """
    This method ensures that is the same month of the same year
    """
    return date_1.month == date_2.month and  date_1.year == date_2.year

## ATTENTION: Do not use this one for new developments ##
# It is flawed, as even though the returned value is DST-safe,
# it is in the _local timezone_, meaning that the number of seconds
# returned is the one for the hour with the same "value" for the
# local timezone.

def int_timestamp(datetimeVal, tz = pytz.timezone('UTC')):
    """
    Returns the number of seconds from the local epoch to the UTC time
    """
    return int(time.mktime(datetimeVal.astimezone(tz).timetuple()))

##
