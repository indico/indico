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

"""
Conversion functions for fossils
"""

import pytz
from MaKaC.user import Avatar


class Conversion(object):

    @classmethod
    def datetime(cls, dt, tz=None, convert=False):
        if dt:
            if tz:
                if isinstance(tz, basestring):
                    tz = pytz.timezone(tz)
                date = dt.astimezone(tz)
            else:
                date = dt
            if convert:
                return {'date': str(date.date()), 'time': str(date.time()), 'tz': str(date.tzinfo)}
            else:
                return date
        else:
            return None

    @classmethod
    def naive(cls, dt, tz=None, naiveTZ=None):
        if dt:
            if tz:
                if isinstance(tz, basestring):
                    tz = pytz.timezone(tz)

                if isinstance(naiveTZ, basestring):
                    naiveTZ = pytz.timezone(naiveTZ)

                date = naiveTZ.localize(dt).astimezone(tz)
            else:
                date = dt
            return date
        else:
            return None

    @classmethod
    def duration(cls, duration, units='minutes', truncate=True):
        if duration:
            from MaKaC.common.utils import formatDuration
            return formatDuration(duration, units, truncate)
        else:
            return None

    @classmethod
    def roomName(cls, room):
        if room:
            return room.getName()
        else:
            return ''

    @classmethod
    def roomFullName(cls, room):
        if room:
            return room.getFullName()
        else:
            return ''

    @classmethod
    def locationName(cls, loc):
        if loc:
            return loc.getName()
        else:
            return ''

    @classmethod
    def locationAddress(cls, loc):
        if loc:
            return loc.getAddress()
        else:
            return ''

    @classmethod
    def parentSession(cls, entry):
        from MaKaC.schedule import ContribSchEntry, BreakTimeSchEntry
        from MaKaC.conference import SessionSlot

        session = None
        owner = entry.getOwner()

        if type(entry) == ContribSchEntry or (type(entry) == BreakTimeSchEntry and type(owner) == SessionSlot):
            session = owner.getSession()

        if session:
            return session.getId()
        else:
            return None

    @classmethod
    def parentSessionCode(cls, entry):
        from MaKaC.schedule import ContribSchEntry, BreakTimeSchEntry
        from MaKaC.conference import SessionSlot, Contribution

        session = None
        owner = entry.getOwner()

        if isinstance(owner, (SessionSlot, Contribution)):
            session = owner.getSession()

        if session:
            return session.getCode()
        else:
            return None

    @classmethod
    def parentSlot(cls, entry):
        from MaKaC.schedule import ContribSchEntry, BreakTimeSchEntry
        from MaKaC.conference import SessionSlot#, Session

        slot = None

        if type(entry) == ContribSchEntry and entry.getSchedule() is not None:
            slot = entry.getSchedule().getOwner()

        elif type(entry) == BreakTimeSchEntry:
            slot = entry.getOwner()

        if slot and type(slot) == SessionSlot:
            return slot.getId()
        else:
            return None

    @classmethod
    def sessionList(cls, event):
        sessions = {}
        for session in event.getSessionList():
            sessions[session.getId()] = session;
        return sessions

    @classmethod
    def locatorString(cls, obj):

        locator = obj.getOwner().getLocator()
        if not locator.has_key('sessionId'):
            if locator.has_key('contribId'):
                return "c%(contribId)s" % locator
            else:
                return ""
        elif not locator.has_key('contribId'):
            return "s%(sessionId)sl%(slotId)s" % locator
        else:
            return "s%(sessionId)sc%(contribId)s" % locator

    @classmethod
    def timedelta(cls, obj):
        """
        Converts a timedelta to integer minutes
        """
        return int(obj.seconds / 60)

    @classmethod
    def reservationsList(cls, resvs):
        res = {}
        for resv in resvs:
            if not res.has_key(resv.room.getFullName()):
                res[resv.room.getFullName()] = []
            res[resv.room.getFullName()].extend([{'startDateTime': cls.datetime(period.startDT), 'endDateTime':  cls.datetime(period.endDT)} for period in resv.splitToPeriods()])
        return res

    @classmethod
    def iterable(cls, conversion):
        def iter(iteList):
            res = []
            for i in iteList:
                res.append(conversion(i))
            return res
        return iter

    @classmethod
    def url(cls, handler):
        def _url(locator):
            return str(handler.getURL(**locator))
        return _url

    @classmethod
    def visibility(cls, conf):
        visibility = conf.getVisibility()
        path = conf.getOwnerPath()
        if visibility == 0:
            id = ""
            name = "Nowhere"
        elif visibility > len(path):
            id = ""
            name = "Everywhere"
        else:
            categ = path[conf.getVisibility()-1]
            id = categ.getId()
            name = categ.getTitle()
        return {'id': id,
                'name': name}

    @classmethod
    def getReportNumbers(cls, obj):
        from MaKaC.common import utils
        return utils.getReportNumberItems(obj)

    @classmethod
    def allowedList(cls, obj):
        allowed_emails = []
        allowed_groups = []
        for allowed in obj.getRecursiveAllowedToAccessList():
            if isinstance(allowed, Avatar):
                allowed_emails.extend(allowed.getEmails())
            else:
                allowed_groups.append(allowed.getId())

        return {'users': allowed_emails,
                'groups': allowed_groups}
