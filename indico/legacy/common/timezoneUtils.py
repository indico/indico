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

from datetime import datetime

from flask import session, has_request_context
from pytz import timezone

from indico.core.config import Config


def nowutc():
    return timezone('UTC').localize(datetime.utcnow())


def utc2server(date, naive=True):
    date = date.replace(tzinfo=None)
    servertz = Config.getInstance().getDefaultTimezone()
    servertime = timezone('UTC').localize(date).astimezone(timezone(servertz))
    if naive:
        return servertime.replace(tzinfo=None)
    return servertime


class DisplayTZ:
    def __init__(self, aw=None, conf=None, useServerTZ=0):
        from indico.modules.events.legacy import LegacyConference
        if not has_request_context():
            sessTimezone = 'LOCAL'
        else:
            sessTimezone = session.timezone
        if sessTimezone == 'LOCAL':
            if useServerTZ == 0 and conf is not None:
                # conf can be Event, Conference or Category
                if isinstance(conf, LegacyConference):
                    conf = conf.as_event
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
