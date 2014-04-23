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
Base export interface
"""

# python stdlib imports
import itertools
import pytz
import re
import urllib
from datetime import datetime, timedelta, time
from flask import request
from types import GeneratorType
from ZODB.POSException import ConflictError

# indico imports
from indico.core.db import DBMgr
from indico.util.date_time import nowutc
from indico.util.fossilize import fossilize
from indico.web.http_api.metadata import Serializer
from indico.web.http_api.metadata.html import HTML4Serializer
from indico.web.http_api.metadata.jsonp import JSONPSerializer
from indico.web.http_api.metadata.ical import ICalSerializer
from indico.web.http_api.metadata.atom import AtomSerializer
from indico.web.http_api.responses import HTTPAPIError
from indico.web.http_api.util import get_query_parameter
from indico.web.http_api.exceptions import ArgumentParseError, LimitExceededException

# indico legacy imports
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.plugins.base import PluginsHolder
from MaKaC.common.logger import Logger


class HTTPAPIHook(object):
    """This class is the hook between the query (path+params) and the generator of the results (fossil).
       It is also in charge of checking the parameters and the access rights.
    """

    HOOK_LIST = []
    TYPES = None  # abstract
    PREFIX = 'export'  # url prefix. must exist in indico.web.flask.blueprints.api, too! also used as function prefix
    RE = None  # abstract
    DEFAULT_DETAIL = None  # abstract
    MAX_RECORDS = {}
    SERIALIZER_TYPE_MAP = {}  # maps fossil type names to friendly names (useful for plugins e.g. RoomCERN --> Room)
    VALID_FORMATS = None  # None = all formats
    GUEST_ALLOWED = True  # When False, it forces authentication
    COMMIT = False  # commit database changes
    HTTP_POST = False  # require (and allow) HTTP POST
    NO_CACHE = False

    @classmethod
    def parseRequest(cls, path, queryParams):
        """Parse a request path and return a hook and the requested data type."""
        path = urllib.unquote(path)
        hooks = itertools.chain(cls.HOOK_LIST, cls._getPluginHooks())
        for expCls in hooks:
            Logger.get('HTTPAPIHook.parseRequest').debug(expCls)
            m = expCls._matchPath(path)
            if m:
                gd = m.groupdict()
                g = m.groups()
                type = g[0]
                format = g[-1]
                if format not in DataFetcher.getAllowedFormats():
                    return None, None
                elif expCls.VALID_FORMATS and format not in expCls.VALID_FORMATS:
                    return None, None
                return expCls(queryParams, type, gd), format
        return None, None

    @staticmethod
    def register(cls):
        """Register a hook that is not part of a plugin.

        To use it, simply decorate the hook class with this method."""
        assert cls.RE is not None
        HTTPAPIHook.HOOK_LIST.append(cls)
        return cls

    @classmethod
    def _matchPath(cls, path):
        if not hasattr(cls, '_RE'):
            types = '|'.join(cls.TYPES)
            cls._RE = re.compile(r'/' + cls.PREFIX + '/(' + types + r')/' + cls.RE + r'\.(\w+)$')
        return cls._RE.match(path)

    @classmethod
    def _getPluginHooks(cls):
        for plugin in PluginsHolder().getPluginTypes():
            for expClsName in plugin.getHTTPAPIHookList():
                yield getattr(plugin.getModule().http_api, expClsName)

    def __init__(self, queryParams, type, pathParams):
        self._queryParams = queryParams
        self._type = type
        self._pathParams = pathParams

    def _getParams(self):
        self._offset = get_query_parameter(self._queryParams, ['O', 'offset'], 0, integer=True)
        self._orderBy = get_query_parameter(self._queryParams, ['o', 'order'])
        self._descending = get_query_parameter(self._queryParams, ['c', 'descending'], 'no') == 'yes'
        self._detail = get_query_parameter(self._queryParams, ['d', 'detail'], self.DEFAULT_DETAIL)
        tzName = get_query_parameter(self._queryParams, ['tz'], None)

        info = HelperMaKaCInfo.getMaKaCInfoInstance()
        self._serverTZ = info.getTimezone()

        if tzName is None:
            tzName = self._serverTZ
        try:
            self._tz = pytz.timezone(tzName)
        except pytz.UnknownTimeZoneError, e:
            raise HTTPAPIError("Bad timezone: '%s'" % e.message, 400)
        max = self.MAX_RECORDS.get(self._detail, 1000)
        self._userLimit = get_query_parameter(self._queryParams, ['n', 'limit'], 0, integer=True)
        if self._userLimit > max:
            raise HTTPAPIError("You can only request up to %d records per request with the detail level '%s'" %
                               (max, self._detail), 400)
        self._limit = self._userLimit if self._userLimit > 0 else max

        fromDT = get_query_parameter(self._queryParams, ['f', 'from'])
        toDT = get_query_parameter(self._queryParams, ['t', 'to'])
        dayDT = get_query_parameter(self._queryParams, ['day'])

        if (fromDT or toDT) and dayDT:
            raise HTTPAPIError("'day' can only be used without 'from' and 'to'", 400)
        elif dayDT:
            fromDT = toDT = dayDT

        self._fromDT = DataFetcher._getDateTime('from', fromDT, self._tz) if fromDT else None
        self._toDT = DataFetcher._getDateTime('to', toDT, self._tz, aux=self._fromDT) if toDT else None

    def _hasAccess(self, aw):
        return True

    def _getMethodName(self):
        return self.PREFIX + '_' + self._type

    def _performCall(self, func, aw):
        resultList = []
        complete = True
        try:
            res = func(aw)
            if isinstance(res, GeneratorType):
                for obj in res:
                    resultList.append(obj)
            else:
                resultList = res
        except LimitExceededException:
            complete = (self._limit == self._userLimit)
        return resultList, complete

    def __call__(self, aw):
        """Perform the actual exporting"""
        if self.HTTP_POST != (request.method == 'POST'):
            raise HTTPAPIError('This action requires %s' % ('POST' if self.HTTP_POST else 'GET'), 405)
        self._getParams()
        if not self.GUEST_ALLOWED and not aw.getUser():
            raise HTTPAPIError('Guest access to this resource is forbidden.', 403)
        if not self._hasAccess(aw):
            raise HTTPAPIError('Access to this resource is restricted.', 403)

        method_name = self._getMethodName()
        func = getattr(self, method_name, None)
        if not func:
            raise NotImplementedError(method_name)

        if not self.COMMIT:
            # Just execute the function, we'll never have to repeat it
            resultList, complete = self._performCall(func, aw)
        else:
            # Try it a few times until commit succeeds
            dbi = DBMgr.getInstance()
            for _retry in xrange(10):
                dbi.sync()
                resultList, complete = self._performCall(func, aw)
                try:
                    dbi.commit()
                except ConflictError:
                    pass  # retry
                else:
                    break
            else:
                raise HTTPAPIError('An unresolvable database conflict has occured', 500)

        extraFunc = getattr(self, method_name + '_extra', None)
        extra = extraFunc(aw, resultList) if extraFunc else None
        return resultList, extra, complete, self.SERIALIZER_TYPE_MAP


class DataFetcher(object):

    _deltas = {'yesterday': timedelta(-1),
               'tomorrow': timedelta(1)}

    _sortingKeys = {'id': lambda x: x.getId(),
                    'start': lambda x: x.getStartDate(),
                    'end': lambda x: x.getEndDate(),
                    'title': lambda x: x.getTitle()}

    def __init__(self, aw, hook):
        self._aw = aw
        self._hook = hook

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

            atoms = list(0 if a is None else int(a) * mod for a in m.groups()[1:])
            if atoms[1] > 23 or atoms[2] > 59:
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
            rel, value = cls._parseDateTime(dateTime, ctx == 'from')
        except ArgumentParseError, e:
            raise HTTPAPIError(e.message, 400)

        if rel == 'abs':
            return tz.localize(value) if not value.tzinfo else value
        elif rel == 'ctx' and type(value) == timedelta:
            value = nowutc() + value

        # from here on, 'value' has to be a datetime
        if ctx == 'from':
            return tz.localize(value.combine(value.date(), time(0, 0, 0)))
        else:
            return tz.localize(value.combine(value.date(), time(23, 59, 59)))


class IteratedDataFetcher(DataFetcher):
    DETAIL_INTERFACES = {}
    FULL_SORTING_TIMEFRAME = timedelta(weeks=4)

    def __init__(self, aw, hook):
        super(IteratedDataFetcher, self).__init__(aw, hook)
        self._tz = hook._tz
        self._serverTZ = hook._serverTZ
        self._offset = hook._offset
        self._limit = hook._limit
        self._detail = hook._detail
        self._orderBy = hook._orderBy
        self._descending = hook._descending
        self._fromDT = hook._fromDT
        self._toDT = hook._toDT

    def _userAccessFilter(self, obj):
        return obj.canAccess(self._aw)

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
        if orderBy or descending:
            sortingKey = self._sortingKeys.get(orderBy)
            if self._toDT and self._fromDT and self._toDT - self._fromDT <= self.FULL_SORTING_TIMEFRAME:
                # If the timeframe is not too big we sort the whole dataset and limit it afterwards. Ths results in
                # better results but worse performance.
                limitedIterable = self._limitIterator(sorted(iterator, key=sortingKey, reverse=descending), limit)
            else:
                try:
                    limitedIterable = sorted(self._limitIterator(iterator, limit),
                                             key=sortingKey, reverse=descending)
                except LimitExceededException:
                    exceeded = True
                    limitedIterable = sorted(self._intermediateResults,
                                             key=sortingKey, reverse=descending)
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

    def _makeFossil(self, obj, iface):
        return fossilize(obj, iface, tz=self._tz, naiveTZ=self._serverTZ,
                         filters={'access': self._userAccessFilter},
                         mapClassType={'AcceptedContribution': 'Contribution'})

    def _process(self, iterator, filter=None, iface=None):
        if iface is None:
            iface = self.DETAIL_INTERFACES.get(self._detail)
            if iface is None:
                raise HTTPAPIError('Invalid detail level: %s' % self._detail, 400)
        for obj in self._iterateOver(iterator, self._offset, self._limit, self._orderBy, self._descending, filter):
            yield self._postprocess(obj, self._makeFossil(obj, iface), iface)


Serializer.register('html', HTML4Serializer)
Serializer.register('jsonp', JSONPSerializer)
Serializer.register('ics', ICalSerializer)
Serializer.register('atom', AtomSerializer)
