# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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
Base export interface
"""

import re
import urllib
from datetime import datetime, time, timedelta
from types import GeneratorType

import pytz
from flask import current_app, request

from indico.core.config import config
from indico.core.db import db
from indico.core.logger import Logger
from indico.core.notifications import flush_email_queue, init_email_queue
from indico.util.date_time import now_utc
from indico.web.http_api.exceptions import ArgumentParseError, LimitExceededException
from indico.web.http_api.metadata import Serializer
from indico.web.http_api.metadata.atom import AtomSerializer
from indico.web.http_api.metadata.html import HTML4Serializer
from indico.web.http_api.metadata.ical import ICalSerializer
from indico.web.http_api.metadata.jsonp import JSONPSerializer
from indico.web.http_api.responses import HTTPAPIError
from indico.web.http_api.util import get_query_parameter


class HTTPAPIHook(object):
    """This class is the hook between the query (path+params) and the generator of the results (fossil).
       It is also in charge of checking the parameters and the access rights.
    """

    HOOK_LIST = []
    TYPES = None  # abstract
    PREFIX = 'export'  # url prefix. must exist in indico.web.flask.blueprints.api, too! also used as function prefix
    RE = None  # abstract
    METHOD_NAME = None  # overrides method name derived from prefix+type
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
        hooks = cls.HOOK_LIST
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
                return expCls(queryParams, type, gd, format), format
        return None, None

    @staticmethod
    def register(cls):
        """Register a hook.

        To use it, simply decorate the hook class with this method."""
        assert cls.RE is not None
        HTTPAPIHook.HOOK_LIST.append(cls)
        return cls

    @classmethod
    def _matchPath(cls, path):
        if not hasattr(cls, '_RE'):
            types = '|'.join(cls.TYPES)
            cls._RE = re.compile(r'/' + cls.PREFIX + '/(' + types + r')' + ('/' + cls.RE).rstrip('/') + r'\.(\w+)$')
        return cls._RE.match(path)

    def __init__(self, queryParams, type, pathParams, format):
        self._format = format
        self._queryParams = queryParams
        self._type = type
        self._pathParams = pathParams

    def _getParams(self):
        self._offset = get_query_parameter(self._queryParams, ['O', 'offset'], 0, integer=True)
        if self._offset < 0:
            raise HTTPAPIError('Offset must be a positive number', 400)
        self._orderBy = get_query_parameter(self._queryParams, ['o', 'order'])
        self._descending = get_query_parameter(self._queryParams, ['c', 'descending'], 'no') == 'yes'
        self._detail = get_query_parameter(self._queryParams, ['d', 'detail'], self.DEFAULT_DETAIL)
        tzName = get_query_parameter(self._queryParams, ['tz'], None)

        if tzName is None:
            tzName = config.DEFAULT_TIMEZONE
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

    def _has_access(self, user):
        return True

    @property
    def serializer_args(self):
        return {}

    def _getMethodName(self):
        if self.METHOD_NAME:
            return self.METHOD_NAME
        return self.PREFIX + '_' + self._type.replace('-', '_')

    def _performCall(self, func, user):
        resultList = []
        complete = True
        try:
            res = func(user)
            if isinstance(res, GeneratorType):
                for obj in res:
                    resultList.append(obj)
            else:
                resultList = res
        except LimitExceededException:
            complete = (self._limit == self._userLimit)
        return resultList, complete

    def _perform(self, user, func, extra_func):
        self._getParams()
        if not self._has_access(user):
            raise HTTPAPIError('Access to this resource is restricted.', 403)
        resultList, complete = self._performCall(func, user)
        if isinstance(resultList, current_app.response_class):
            return True, resultList, None, None
        extra = extra_func(user, resultList) if extra_func else None
        return False, resultList, complete, extra

    def __call__(self, user):
        """Perform the actual exporting"""
        if self.HTTP_POST != (request.method == 'POST'):
            raise HTTPAPIError('This action requires %s' % ('POST' if self.HTTP_POST else 'GET'), 405)
        if not self.GUEST_ALLOWED and not user:
            raise HTTPAPIError('Guest access to this resource is forbidden.', 403)

        method_name = self._getMethodName()
        func = getattr(self, method_name, None)
        extra_func = getattr(self, method_name + '_extra', None)
        if not func:
            raise NotImplementedError(method_name)

        if not self.COMMIT:
            is_response, resultList, complete, extra = self._perform(user, func, extra_func)
            db.session.rollback()
        else:
            try:
                init_email_queue()
                is_response, resultList, complete, extra = self._perform(user, func, extra_func)
                db.session.commit()
                flush_email_queue()
            except Exception:
                db.session.rollback()
                raise
        if is_response:
            return resultList
        return resultList, extra, complete, self.SERIALIZER_TYPE_MAP


class DataFetcher(object):
    _deltas = {'yesterday': timedelta(-1),
               'tomorrow': timedelta(1)}

    def __init__(self, user, hook):
        self._user = user
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
        now = now_utc()
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
            value = now_utc() + value

        # from here on, 'value' has to be a datetime
        if ctx == 'from':
            return tz.localize(value.combine(value.date(), time(0, 0, 0)))
        else:
            return tz.localize(value.combine(value.date(), time(23, 59, 59)))


class IteratedDataFetcher(DataFetcher):
    def __init__(self, user, hook):
        super(IteratedDataFetcher, self).__init__(user, hook)
        self._tz = hook._tz
        self._offset = hook._offset
        self._limit = hook._limit
        self._detail = hook._detail
        self._orderBy = hook._orderBy
        self._descending = hook._descending
        self._fromDT = hook._fromDT
        self._toDT = hook._toDT


Serializer.register('html', HTML4Serializer)
Serializer.register('jsonp', JSONPSerializer)
Serializer.register('ics', ICalSerializer)
Serializer.register('atom', AtomSerializer)
