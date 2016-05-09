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

"""
Conversion functions for fossils
"""

from collections import defaultdict

import pytz

from indico.core.db.sqlalchemy.principals import EmailPrincipal
from indico.modules.rb.models.reservation_occurrences import ReservationOccurrence
from indico.modules.groups.legacy import GroupWrapper
from indico.modules.users.legacy import AvatarUserWrapper


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
    def reservationsList(cls, resvs):
        res = defaultdict(list)
        for resv in resvs:
            occurrences = (resv.occurrences
                           .filter(ReservationOccurrence.is_valid)
                           .options(ReservationOccurrence.NO_RESERVATION_USER_STRATEGY))
            res[resv.room.full_name] += [{'startDateTime': cls.datetime(occ.start_dt),
                                          'endDateTime': cls.datetime(occ.end_dt)}
                                         for occ in occurrences]
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
    def allowedList(cls, obj):
        allowed_emails = []
        allowed_groups = []
        for allowed in obj.getRecursiveAllowedToAccessList():
            if isinstance(allowed, AvatarUserWrapper):
                allowed_emails.extend(allowed.getEmails())
            elif isinstance(allowed, EmailPrincipal):
                allowed_emails.append(allowed.email)
            elif isinstance(allowed, GroupWrapper):
                allowed_groups.append(allowed.getId())

        return {'users': allowed_emails,
                'groups': allowed_groups}

    @classmethod
    def addLegacyMinutes(cls, result, _obj=None):
        from indico.modules.events.notes.util import build_note_legacy_api_data
        data = build_note_legacy_api_data(_obj.note)
        if data:
            result.append(data)
        return result
