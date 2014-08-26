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

from datetime import datetime
from functools import wraps
from dateutil.relativedelta import MO, TU, WE, TH, FR
from dateutil.rrule import rrule, DAILY

from indico.core.errors import IndicoError
from indico.core.logger import Logger


def unimplemented(exceptions=(Exception,), message='Unimplemented'):
    def _unimplemented(func):
        @wraps(func)
        def _wrapper(*args, **kw):
            try:
                return func(*args, **kw)
            except exceptions:
                raise IndicoError(str(message))

        return _wrapper

    return _unimplemented


def next_work_day(dtstart=None, neglect_time=True):
    if not dtstart:
        dtstart = datetime.utcnow()
    if neglect_time:
        dtstart = datetime.combine(dtstart.date(), datetime.min.time())
    return list(rrule(DAILY, count=1, byweekday=(MO, TU, WE, TH, FR), dtstart=dtstart))[0]


def proxy_to_reservation_if_single_occurrence(f):
    """Forwards a method call to `self.reservation` if there is only one occurrence."""
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        if not kwargs.pop('propagate', True):
            return f(self, *args, **kwargs)
        resv_func = getattr(self.reservation, f.__name__)
        if not self.reservation.is_repeating:
            return resv_func(*args, **kwargs)
        valid_occurrences = self.reservation.occurrences.filter_by(is_valid=True).limit(2).all()
        if len(valid_occurrences) == 1 and valid_occurrences[0] == self:
            # If we ever use this outside ReservationOccurrence we can probably get rid of the ==self check
            return resv_func(*args, **kwargs)
        return f(self, *args, **kwargs)

    return wrapper


class Serializer(object):
    __public__ = []

    def to_serializable(self, attr='__public__', converters=None):
        serializable = {}
        if converters is None:
            converters = {}
        for k in getattr(self, attr):
            try:
                if isinstance(k, tuple):
                    k, name = k
                else:
                    k, name = k, k

                v = getattr(self, k)
                if callable(v):  # to make it generic, we can get rid of it by properties
                    v = v()
                if isinstance(v, Serializer):
                    v = v.to_serializable()
                elif isinstance(v, list):
                    v = [e.to_serializable() for e in v]
                elif isinstance(v, dict):
                    v = dict((k, vv.to_serializable() if isinstance(vv, Serializer) else vv)
                             for k, vv in v.iteritems())
                if type(v) in converters:
                    v = converters[type(v)](v)
                serializable[name] = v
            except Exception:
                msg = 'Could not retrieve {}.{}.'.format(self.__class__.__name__, k)
                Logger.get('Serializer{}'.format(self.__class__.__name__)).exception(msg)
                raise IndicoError(msg)
        return serializable
