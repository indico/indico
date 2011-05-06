# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010 CERN.
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

"""
Main export interface
"""

# python stdlib imports
import re
from zope.interface import Interface, implements
from datetime import datetime, timedelta, date, time

# external lib imports
import pytz
from simplejson import dumps

# indico imports
from indico.util.date_time import nowutc
from indico.util.fossilize import fossilize

from indico.util.metadata import Serializer
from indico.web.http_api.html import HTML4Serializer
from indico.web.http_api.jsonp import JSONPSerializer
from indico.web.http_api.fossils import IConferenceMetadataFossil

# indico legacy imports
from MaKaC.common.indexes import IndexesHolder
from MaKaC.common.info import HelperMaKaCInfo


from indico.web.http_api.util import get_query_parameter, remove_lists


class ArgumentParseError(Exception):
    pass


class ArgumentValueError(Exception):
    pass


class IExport(Interface):

    def category(cls, idlist, fromDT, toDT, location=None, limit=None,
               orderBy=None, descending=False, detail="events"):
        """
        TODO: Document this
        """

    def event(cls, idlist, orderBy=None, descending=False, detail="events"):
        """
        TODO: Document this
        """


class ExportInterface(object):
    implements(IExport)

    _deltas =  {'yesterday': timedelta(-1),
                'tomorrow': timedelta(1)}

    def __init__(self, dbi):
        self._dbi = dbi

    @classmethod
    def getAllowedFormats(cls):
        return Serializer.getAllFormats()

    @classmethod
    def _parseDateTime(cls, dateTime):
        """
        Accepted formats:
         * ISO 8601 subset - YYYY-MM-DD[THH:MM]
         * 'today', 'yesterday', 'tomorrow' and 'now'
         * days in the future/past: '[+/-]DdHHhMMm'

         'ctx' means that the date will change according to its function
         ('from' or 'to')
        """

        # if it's a an "alias", return immediately
        now = nowutc()
        if dateTime in cls._deltas:
            return ('ctx', now + cls._deltas[dateTime])
        elif dateTime == 'now':
            return ('abs', now)
        elif dateTime == 'today':
            return ('ctx', now)

        m = re.match(r'^(?:(\d{1,3})d)?(?:(\d{1,2})h)?(?:(\d{1,2})m)?$', dateTime)
        if m:
            atoms = list(0 if a == None else int(a) for a in m.groups())



            if atoms[1] > 23  or atoms[2] > 59:
                raise ArgumentParseError("Invalid time!")
            return ('ctx', timedelta(days=atoms[0], hours=atoms[1], minutes=atoms[2]))
        else:
            # iso 8601 subset
            try:
                return ('abs', datetime.strptime(dateTime, "%Y-%m-%dT%H:%M"))
            except ValueError:
                pass
            try:
                return ('ctx', datetime.strptime(dateTime, "%Y-%m-%d"))
            except ValueError:
                raise ArgumentParseError("Impossible to parse '%s'" % dateTime)

    @classmethod
    def _getDateTime(cls, ctx, dateTime, tz, aux=None):

        rel, value = cls._parseDateTime(dateTime)

        if rel == 'abs':
            return tz.localize(value)
        elif rel == 'ctx' and type(value) == timedelta:
            if ctx == 'from':
                raise ArgumentValueError("Only 'to' accepts relative times")
            else:
                value = aux + value

        # from here on, 'value' has to be a datetime
        if ctx == 'from':
            return tz.localize(value.combine(value.date(), time(0, 0, 0)))
        else:
            return tz.localize(value.combine(value.date(), time(23, 59, 59)))

    def category(self, idlist, tzName, qdata):

        orderBy = get_query_parameter(qdata, ['o', 'order'])
        descending = get_query_parameter(qdata, ['c', 'descending'], False)
        detail = get_query_parameter(qdata, ['d', 'detail'], 'events')

        fromDT = get_query_parameter(qdata, ['f', 'from'])
        toDT = get_query_parameter(qdata, ['t', 'to'])
        location = get_query_parameter(qdata, ['l', 'location'])
        limit = get_query_parameter(qdata, ['n', 'limit'], integer=True)

        if tzName == None:
            info = HelperMaKaCInfo.getMaKaCInfoInstance()
            tzName = info.getTimezone()

        tz = pytz.timezone(tzName)

        fromDT = ExportInterface._getDateTime('from', fromDT, tz) if fromDT != None else None
        toDT = ExportInterface._getDateTime('to', toDT, tz, aux=fromDT) if toDT != None else None

        idx = IndexesHolder().getById('categoryDate')

        results = []
        counter = 0
        terminate = False
        # this set acts as a checklist to know if a record has already been sent
        exclude = set()

        for catId in idlist:
            for obj in idx.iterateObjectsIn(catId, fromDT, toDT):
                # TODO: hard limit
                if limit and counter >= limit:
                    terminate = True
                    break
                if obj not in exclude:
                    results.append(fossilize(obj, IConferenceMetadataFossil, tz=tz))
                    exclude.add(obj)
                    counter += 1
            if terminate:
                break

        return results

    def event(self, idlist, orderBy=None, descending=False, detail="events"):
        """
        TODO: Document this
        """

Serializer.register('html', HTML4Serializer)
Serializer.register('jsonp', JSONPSerializer)
