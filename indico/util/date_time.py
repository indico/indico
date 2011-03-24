# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

import time, pytz, calendar

from MaKaC.common.timezoneUtils import nowutc


def utc_timestamp(datetimeVal):
    return int(calendar.timegm(datetimeVal.utctimetuple()))


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
