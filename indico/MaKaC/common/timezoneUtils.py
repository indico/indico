# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

import calendar
import time
from datetime import datetime

from flask import session, has_request_context
from pytz import timezone, all_timezones

from indico.core.config import Config


def nowutc():
    return timezone('UTC').localize(datetime.utcnow())


def server2utc(date):
    servertz = Config.getInstance().getDefaultTimezone()
    return timezone(servertz).localize(date).astimezone(timezone('UTC'))


def utc2server(date, naive=True):
    date = date.replace(tzinfo=None)
    servertz = Config.getInstance().getDefaultTimezone()
    servertime = timezone('UTC').localize(date).astimezone(timezone(servertz))
    if naive:
        return servertime.replace(tzinfo=None)
    return servertime


def date2utctimestamp(date):
    """ Note by DavidMC: I believe this implementation is flawed. At least in my PC
        it is not correct. I think the result depends on the local time of the PC
        executing it. Use timezoneUtils.datetimeToUnixTime & timezoneUtils.unixTimeToDatetime instead.
        As a test, try the 13th February 2009 at 23:31:30 UTC, the timestamp should be 1234567890.
        With this function it's 1234564290 .
    """
    return int(time.mktime(date.utctimetuple()))


def utctimestamp2date(ts):
    """ Note by DavidMC: This function returns a naive datetime.
        You should use timezoneUtils.unixTimeToDatetime instead.
    """
    return datetime.utcfromtimestamp(ts)


def isTimezoneAware(datetime):
    """ Takes a datetime object and returns True if it is timezone-aware (has tzinfo)
        or False if it is naive
    """
    return hasattr(datetime, 'tzinfo') and datetime.tzinfo is not None


def naive2local(naiveDateTime, localTimezone):
    """ Extends naive datetimes with the specified timezone info (string),
        using DST or STD according to the date in question

    >>> from datetime import datetime
    >>> naive2local(datetime(2008,12,25,0,0,0), 'Europe/Zurich')
    datetime.datetime(2008, 12, 25, 1, 0, tzinfo=<DstTzInfo 'Europe/Zurich' CET+1:00:00 STD>)
    >>> naive2local(datetime(2008,8,25,0,0,0), 'Europe/Zurich')
    datetime.datetime(2008, 8, 25, 2, 0, tzinfo=<DstTzInfo 'Europe/Zurich' CEST+2:00:00 DST>)
    """

    utcDateTime = naiveDateTime.replace(microsecond=0, tzinfo=timezone('UTC'))
    localDateTime = utcDateTime.astimezone(timezone(localTimezone))
    return localDateTime


def setAdjustedDate(date, object=None, tz=None):
    # Localizes a date to the timezone tz
    # tz can be a string (preferred) or a pytz.timezone object
    # If tz is None, the timezone of the object is used
    if not tz:
        tz = object.getTimezone()
    if isinstance(tz, basestring):
        tz = timezone(tz)
    if tz.zone not in all_timezones:
        tz = timezone('UTC')
    return tz.localize(date).astimezone(timezone('UTC'))


def getAdjustedDate(date, object=None, tz=None):
    # Returns a date adjusted to the timezone tz
    # tz can be string (preferred) or a pytz.timezone object
    # If tz is None, the timezone of the object is used
    if not tz:
        tz = object.getTimezone()
    if isinstance(tz, basestring):
        tz = timezone(tz)
    if tz.zone not in all_timezones:
        tz = timezone('UTC')
    return date.astimezone(tz)


def datetimeToUnixTime(t):
    """ Gets a datetime object
        Returns a float with the number of seconds from the UNIX epoch
    """
    return calendar.timegm(t.utctimetuple()) + t.microsecond / 1000000.0


def datetimeToUnixTimeInt(t):
    """ Gets a datetime object
        Returns an int with the number of seconds from the UNIX epoch
    """
    return calendar.timegm(t.utctimetuple())


def unixTimeToDatetime(seconds, tz='UTC'):
    """ Gets a float (or an object able to be turned into a float) representing the seconds from the UNIX epoch,
        and a string representing the timezone (UTC) by default.
        Returns a datetime object
    """
    return datetime.fromtimestamp(float(seconds), timezone(tz))


class DisplayTZ:

    def __init__(self, aw=None, conf=None, useServerTZ=0):
        if not has_request_context():
            sessTimezone = 'LOCAL'
        else:
            sessTimezone = session.timezone
        if sessTimezone == 'LOCAL':
            if useServerTZ == 0 and conf is not None:
                sessTimezone = getattr(conf, 'timezone', 'UTC')
            else:
                sessTimezone = Config.getInstance().getDefaultTimezone()
        self._displayTZ = sessTimezone
        if not self._displayTZ:
            self._displayTZ = Config.getInstance().getDefaultTimezone()

    def getDisplayTZ(self, as_timezone=False):
        return timezone(self._displayTZ) if as_timezone else self._displayTZ


class SessionTZ:

    def __init__(self, user):
        try:
            displayMode = user.getDisplayTZMode()
        except:
            displayMode = 'MyTimezone'
        if displayMode == 'MyTimezone':
            try:
                tz = user.getTimezone()
            except:
                tz = "LOCAL"
        else:
            tz = "LOCAL"
        self._displayTZ = tz

    def getSessionTZ(self):
        return self._displayTZ
