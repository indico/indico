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
import fnmatch
import itertools
import pytz
import re
from zope.interface import Interface, implements
from datetime import datetime, timedelta, date, time

# external lib imports
from simplejson import dumps

# indico imports
from indico.util.date_time import nowutc
from indico.util.fossilize import fossilize

from indico.util.metadata import Serializer
from indico.web.http_api.html import HTML4Serializer
from indico.web.http_api.jsonp import JSONPSerializer
from indico.web.http_api.ical import ICalSerializer
from indico.web.http_api.atom import AtomSerializer
from indico.web.http_api.fossils import IConferenceMetadataFossil,\
    IConferenceMetadataWithContribsFossil, IConferenceMetadataWithSubContribsFossil,\
    IConferenceMetadataWithSessionsFossil, IPeriodFossil
from indico.web.http_api.responses import HTTPAPIError
from indico.web.wsgi import webinterface_handler_config as apache

# indico legacy imports
from MaKaC.common.indexes import IndexesHolder
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.conference import ConferenceHolder
from MaKaC.plugins.base import PluginsHolder
from MaKaC.rb_tools import Period, datespan

from indico.web.http_api.util import get_query_parameter, remove_lists

MAX_DATETIME = datetime(2099, 12, 31, 23, 59, 00)
MIN_DATETIME = datetime(2000, 1, 1, 00, 00, 00)

class ArgumentParseError(Exception):
    pass


class ArgumentValueError(Exception):
    pass


class LimitExceededException(Exception):
    pass


class Exporter(object):
    EXPORTER_LIST = []
    TYPES = None # abstract
    RE = None # abstract
    DEFAULT_DETAIL = None # abstract
    MAX_RECORDS = None # abstract
    SERIALIZER_TYPE_MAP = {}
    VALID_FORMATS = None # None = all formats

    @classmethod
    def parseRequest(cls, path, qdata):
        """Parse a request path and return an exporter and the requested data type."""
        exporters = itertools.chain(cls.EXPORTER_LIST, cls._getPluginExporters())
        for expCls in exporters:
            m = expCls._matchPath(path)
            if m:
                gd = m.groupdict()
                g = m.groups()
                type = g[0]
                format = g[-1]
                if format not in ExportInterface.getAllowedFormats():
                    return None, None
                elif expCls.VALID_FORMATS and format not in expCls.VALID_FORMATS:
                    return None, None
                return expCls(qdata, type, gd), format
        return None, None

    @staticmethod
    def register(cls):
        """Register an exporter that is not part of a plugin.

        To use it, simply decorate the exporter class with this method."""
        assert cls.RE is not None
        Exporter.EXPORTER_LIST.append(cls)
        return cls

    @classmethod
    def _matchPath(cls, path):
        if not hasattr(cls, '_RE'):
            types = '|'.join(cls.TYPES)
            cls._RE = re.compile(r'/export/(' + types + r')/' + cls.RE + r'\.(\w+)$')
        return cls._RE.match(path)

    @classmethod
    def _getPluginExporters(cls):
        for plugin in PluginsHolder().getPluginTypes():
            for expClsName in plugin.getExporterList():
                yield getattr(plugin.getModule().export, expClsName)

    def __init__(self, qdata, type, urlParams):
        self._qdata = qdata
        self._type = type
        self._urlParams = urlParams

    def _getParams(self):
        self._offset = get_query_parameter(self._qdata, ['O', 'offset'], 0, integer=True)
        self._orderBy = get_query_parameter(self._qdata, ['o', 'order'], 'start')
        self._descending = get_query_parameter(self._qdata, ['c', 'descending'], False)
        self._detail = get_query_parameter(self._qdata, ['d', 'detail'], self.DEFAULT_DETAIL)
        tzName = get_query_parameter(self._qdata, ['tz'], None)

        info = HelperMaKaCInfo.getMaKaCInfoInstance()
        self._serverTZ = info.getTimezone()

        if tzName is None:
            tzName = self._serverTZ
        try:
            self._tz = pytz.timezone(tzName)
        except pytz.UnknownTimeZoneError, e:
            raise HTTPAPIError("Bad timezone: '%s'" % e.message, apache.HTTP_BAD_REQUEST)
        max = self.MAX_RECORDS.get(self._detail, 10000)
        self._userLimit = get_query_parameter(self._qdata, ['n', 'limit'], 0, integer=True)
        if self._userLimit > max:
            raise HTTPAPIError("You can only request up to %d records per request with the detail level '%s'" %
                (max, self._detail), apache.HTTP_BAD_REQUEST)
        self._limit = self._userLimit if self._userLimit > 0 else max

    def __call__(self, aw):
        """Perform the actual exporting"""
        self._getParams()
        resultList = []
        complete = True

        func = getattr(self, 'export_' + self._type, None)
        if not func:
            raise NotImplementedError('export_' + self._type)

        try:
            for obj in func(aw):
                resultList.append(obj)
        except LimitExceededException:
            complete = (self._limit == self._userLimit)

        return resultList, complete, self.SERIALIZER_TYPE_MAP


class ExportInterface(object):
    DETAIL_INTERFACES = {}

    _deltas =  {'yesterday': timedelta(-1),
                'tomorrow': timedelta(1)}

    _sortingKeys = {'id': lambda x: x.getId(),
                    'end': lambda x: x.getEndDate(),
                    'title': lambda x: x.getTitle()}

    def __init__(self, aw, exporter):
        self._aw = aw
        self._tz = exporter._tz
        self._serverTZ = exporter._serverTZ
        self._offset = exporter._offset
        self._limit = exporter._limit
        self._detail = exporter._detail
        self._orderBy = exporter._orderBy
        self._descending = exporter._descending

    @classmethod
    def getAllowedFormats(cls):
        return Serializer.getAllFormats()

    @classmethod
    def _parseDateTime(cls, dateTime, allowNegativeOffset):
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

        m = re.match(r'^([+-])?(?:(\d{1,3})d)?(?:(\d{1,2})h)?(?:(\d{1,2})m)?$', dateTime)
        if m:
            mod = -1 if m.group(1) == '-' else 1
            if not allowNegativeOffset and mod == -1:
                raise ArgumentParseError('End date cannot be a negative offset')

            atoms = list(0 if a == None else int(a) * mod for a in m.groups()[1:])
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

        try:
            rel, value = cls._parseDateTime(dateTime, ctx=='from')
        except ArgumentParseError, e:
            raise HTTPAPIError(e.message, apache.HTTP_BAD_REQUEST)

        if rel == 'abs':
            return tz.localize(value) if not value.tzinfo else value
        elif rel == 'ctx' and type(value) == timedelta:
            if ctx == 'from':
                value = nowutc() + value
            else:
                value = aux + value

        # from here on, 'value' has to be a datetime
        if ctx == 'from':
            return tz.localize(value.combine(value.date(), time(0, 0, 0)))
        else:
            return tz.localize(value.combine(value.date(), time(23, 59, 59)))

    def _getQueryParams(self, qdata):
        fromDT = get_query_parameter(qdata, ['f', 'from'])
        toDT = get_query_parameter(qdata, ['t', 'to'])
        dayDT = get_query_parameter(qdata, ['day'])

        if (fromDT or toDT) and dayDT:
            raise HTTPAPIError("'day' can only be used without 'from' and 'to'", apache.HTTP_BAD_REQUEST)
        elif dayDT:
            fromDT = toDT = dayDT

        self._fromDT = ExportInterface._getDateTime('from', fromDT, self._tz) if fromDT else None
        self._toDT = ExportInterface._getDateTime('to', toDT, self._tz, aux=self._fromDT) if toDT else None

    def _limitIterator(self, iterator, limit):
        counter = 0
        # this set acts as a checklist to know if a record has already been sent
        exclude = set()
        self._intermediateResults = []

        for obj in iterator:
            if counter >= limit:
                raise LimitExceededException()
            if obj not in exclude and (not hasattr(obj, 'canAccess') or obj.canAccess(self._aw)):
                self._intermediateResults.append(obj)
                yield obj
                exclude.add(obj)
                counter += 1

    def _sortedIterator(self, iterator, limit, orderBy, descending):

        exceeded = False
        if (orderBy and orderBy != 'start') or descending:
            sortingKey = self._sortingKeys.get(orderBy)
            try:
                limitedIterable = sorted(self._limitIterator(iterator, limit),
                                         key=sortingKey)
            except LimitExceededException:
                exceeded = True
                limitedIterable = sorted(self._intermediateResults,
                                         key=sortingKey)

            if descending:
                limitedIterable.reverse()
        else:
            limitedIterable = self._limitIterator(iterator, limit)

        # iterate over result
        for obj in limitedIterable:
            yield obj

        # in case the limit was exceeded while sorting the results,
        # raise the exception as if we were truly consuming an iterator
        if orderBy and exceeded:
            raise LimitExceededException()

    def _iterateOver(self, iterator, offset, limit, orderBy, descending, filter=None):
        """
        Iterates over a maximum of `limit` elements, starting at the
        element number `offset`. The elements will be ordered according
        to `orderby` and `descending` (slooooow) and filtered by the
        callable `filter`:
        """

        if filter:
            iterator = itertools.ifilter(filter, iterator)
        # offset + limit because offset records are skipped and do not count
        sortedIterator = self._sortedIterator(iterator, offset + limit, orderBy, descending)
        # Skip offset elements - http://docs.python.org/library/itertools.html#recipes
        next(itertools.islice(sortedIterator, offset, offset), None)
        return sortedIterator

    def _postprocess(self, obj, fossil, iface):
        return fossil

    def _process(self, iterator, filter=None, iface=None):
        if iface is None:
            iface = self.DETAIL_INTERFACES.get(self._detail)
            if iface is None:
                raise HTTPAPIError('Invalid detail level: %s' % self._detail, apache.HTTP_BAD_REQUEST)
        for obj in self._iterateOver(iterator, self._offset, self._limit, self._orderBy, self._descending, filter):
            yield self._postprocess(obj, fossilize(obj, iface, tz=self._tz, naiveTZ=self._serverTZ), iface)


@Exporter.register
class CategoryEventExporter(Exporter):
    TYPES = ('event', 'categ')
    RE = r'(?P<idlist>\w+(?:-\w+)*)'
    DEFAULT_DETAIL = 'events'
    MAX_RECORDS = {
        'events': 10000,
        'contributions': 500,
        'subcontributions': 500,
        'sessions': 100,
    }

    def _getParams(self):
        super(CategoryEventExporter, self)._getParams()
        self._idList = self._urlParams['idlist'].split('-')

    def export_categ(self, aw):
        expInt = CategoryEventExportInterface(aw, self)
        return expInt.category(self._idList, self._qdata)

    def export_event(self, aw):
        expInt = CategoryEventExportInterface(aw, self)
        return expInt.event(self._idList, self._qdata)


class CategoryEventExportInterface(ExportInterface):
    DETAIL_INTERFACES = {
        'events': IConferenceMetadataFossil,
        'contributions': IConferenceMetadataWithContribsFossil,
        'subcontributions': IConferenceMetadataWithSubContribsFossil,
        'sessions': IConferenceMetadataWithSessionsFossil
    }

    def _getQueryParams(self, qdata):
        super(CategoryEventExportInterface, self)._getQueryParams(qdata)
        self._occurrences = get_query_parameter(qdata, ['occ', 'occurrences'], 'no') == 'yes'

    def _postprocess(self, obj, fossil, iface):
        return self._addOccurrences(fossil, obj, self._fromDT, self._toDT)

    @staticmethod
    def _eventDaysIterator(conf):
        """
        Iterates over the daily times of an event
        """
        sched = conf.getSchedule()
        for day in datespan(conf.getStartDate(), conf.getEndDate()):
            startDT = sched.calculateDayStartDate(day)
            endDT = sched.calculateDayEndDate(day)
            if startDT != endDT:
                yield Period(startDT, endDT)

    def _addOccurrences(self, fossil, obj, startDT, endDT):
        if self._occurrences:
            (startDT, endDT) = (startDT or MIN_DATETIME,
                                endDT or MAX_DATETIME)
            # get occurrences in the date interval
            fossil['occurrences'] = fossilize(itertools.ifilter(
                lambda x: x.startDT >= startDT and x.endDT <= endDT, self._eventDaysIterator(obj)),
                                             {Period: IPeriodFossil}, tz=self._tz, naiveTZ=self._serverTZ)

        return fossil

    def category(self, idlist, qdata):
        self._getQueryParams(qdata)
        location = get_query_parameter(qdata, ['l', 'location'])
        room = get_query_parameter(qdata, ['r', 'room'])

        idx = IndexesHolder().getById('categoryDate')

        filter = None
        if room or location:
            def filter(obj):
                if location:
                    name = obj.getLocation() and obj.getLocation().getName()
                    if not name or not fnmatch.fnmatch(name.lower(), location.lower()):
                        return False
                if room:
                    name = obj.getRoom() and obj.getRoom().getName()
                    if not name or not fnmatch.fnmatch(name.lower(), room.lower()):
                        return False
                return True

        for catId in idlist:
            for obj in self._process(idx.iterateObjectsIn(catId, self._fromDT, self._toDT), filter, IConferenceMetadataFossil):
                yield obj

    def event(self, idlist, qdata):
        self._getQueryParams(qdata)
        ch = ConferenceHolder()

        def _iterate_objs(objIds):
            for objId in objIds:
                obj = ch.getById(objId, True)
                if obj is not None:
                    yield obj

        return self._process(_iterate_objs(idlist))

Serializer.register('html', HTML4Serializer)
Serializer.register('jsonp', JSONPSerializer)
Serializer.register('ics', ICalSerializer)
Serializer.register('atom', AtomSerializer)
