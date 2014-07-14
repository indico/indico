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

"""
Small functions and classes widely used in Room Booking Module.
"""

import json
import random
from datetime import date, datetime
from functools import wraps

from dateutil.relativedelta import MO, TU, WE, TH, FR, SA, SU
from dateutil.rrule import rrule, DAILY
from sqlalchemy.orm import class_mapper
from sqlalchemy.sql import over, func

from MaKaC import user as user_mod
from MaKaC.accessControl import AdminList
from MaKaC.plugins.base import PluginsHolder
from MaKaC.user import Avatar
from indico.core.errors import IndicoError
from indico.core.logger import Logger
from indico.util.decorators import cached_writable_property
from indico.util.i18n import _


def getDefaultValue(cls, attr):
    for p in class_mapper(cls).iterate_properties:
        if p.key == attr:
            if len(p.columns) == 1:
                if p.columns[0].default:
                    return p.columns[0].default.arg
                else:
                    raise RuntimeError('This attribute doesn\'t have a default value')
            else:
                raise RuntimeError('Non or multiple column attribute')
    raise RuntimeError('Attribute couldn\'t be found')


def clone(cls, obj):
    pks = set([c.key for c in class_mapper(cls).primary_key])
    attrs = [p.key for p in class_mapper(cls).iterate_properties if p.key not in pks]
    return cls(**dict((attr, getattr(obj, attr)) for attr in attrs))


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


def versioned_cache(cache, primary_key_attr='id'):
    """Mixin to add a cache version number, bumped on each commit.

    This class MUST come before db.Model in the superclass list::

        class SomeModel(versioned_cache(my_cache), db.Model, ...):
            pass

    :param cache: A :class:`GenericCache` instance
    :param primary_key_attr: The attribute containing the an unique identifier for the object
    """
    def _get_key(obj):
        return 'version:{}[{}]'.format(type(obj).__name__, getattr(obj, primary_key_attr))

    class _CacheVersionMixin(object):
        def __committed__(self, change):
            super(_CacheVersionMixin, self).__committed__(change)
            if change == 'delete':
                cache.delete(_get_key(self))
            else:
                self.cache_version += 1

        @cached_writable_property('_cache_version')
        def cache_version(self):
            return cache.get(_get_key(self), 0)

        @cache_version.setter
        def cache_version(self, value):
            cache.set(_get_key(self), value)

    return _CacheVersionMixin


def cached(cache, primary_key_attr='id', base_ttl=86400*31):
    """Caches the decorated function's result in redis.

    This decorator is meant to be be used for properties::

        @property
        @cached(my_cache)
        def expensive_function(self):
            return self.do_expensive_stuff()

    It is usually a good idea to expunge cache entries when the object is modified.
    To do so, make the model inherit from the mixin created by :func:`versioned_cache`.

    :param cache: A :class:`GenericCache` instance
    :param primary_key_attr: The attribute containing the an unique identifier for the object
    :param base_ttl: The time after which a cached property expires
    """
    def decorator(f):
        @wraps(f)
        def wrapper(self, *args, **kawrgs):
            primary_key = getattr(self, primary_key_attr)
            if hasattr(self, 'cache_version'):
                key = '{}[{}.{}].{}'.format(type(self).__name__, primary_key, self.cache_version, f.__name__)
            else:
                key = '{}[{}].{}'.format(type(self).__name__, primary_key, f.__name__)

            result = cache.get(key)
            if result is None:
                result = f(self, *args, **kawrgs)
                # Cache the value with a somewhat random expiry so we don't end up with all keys
                # expiring at the same time if there hasn't been an update for some time
                cache.set(key, result, base_ttl + 300 * random.randint(0, 200))
            return result

        return wrapper

    return decorator


def getRoomBookingOption(opt):
    return PluginsHolder().getPluginType('RoomBooking').getOption(opt).getValue()


def accessChecked(func):
    """
    Check if user should have access to RB module in general
    """

    def check_access_internal(*args, **kwargs):
        try:
            avatar = args[-1]
        except IndexError:
            raise IndicoError(_('accessChecked decorator expects an avatar as a positional argument'))

        if AdminList.getInstance().isAdmin(avatar):
            return True
        else:
            def isAuthorized(entity):
                if isinstance(entity, user_mod.Group):
                    return entity.containsUser(avatar)
                elif isinstance(entity, Avatar):
                    return entity == avatar
                else:
                    raise RuntimeError('Unexpected entity type')

            authorized_list = getRoomBookingOption('AuthorisedUsersGroups')
            if authorized_list:
                return any(map(isAuthorized, authorized_list))
            else:
                return True

    def check_access(*args, **kwargs):
        if not check_access_internal(*args, **kwargs):
            return False
        return func(*args, **kwargs)

    return check_access


def stats_to_dict(results):
    """ Creates dictionary from stat rows of reservations

        results = [
            is_live(bool),
            is_cancelled(bool),
            is_rejected(bool),
            count(int)
        ]
    """

    stats = {
        'liveValid': 0,
        'liveCancelled': 0,
        'liveRejected': 0,
        'archivedValid': 0,
        'archivedCancelled': 0,
        'archivedRejected': 0
    }
    for is_live, is_cancelled, is_rejected, c in results:
        assert not (is_cancelled and is_rejected)
        if is_live:
            if is_cancelled:
                stats['liveCancelled'] = c
            elif is_rejected:
                stats['liveRejected'] = c
            else:
                stats['liveValid'] = c
        else:
            if is_cancelled:
                stats['oldCancelled'] = c
            elif is_rejected:
                stats['oldRejected'] = c
            else:
                stats['oldValid'] = c
    return stats


class JSONStringBridgeMixin:
    """
    A property to automatically encode/decode a string column to JSON and vice versa.

    Assumes mapped column name is 'raw_data'
    """

    @property
    def value(self):
        return json.loads(self.raw_data)

    @value.setter
    def value(self, data):
        self.raw_data = json.dumps(data)

    @property
    def is_value_required(self):
        return self.value.get('is_required', False)

    @property
    def is_value_hidden(self):
        return self.value.get('is_hidden', False)

    @property
    def is_value_used(self):
        return self.value.get('is_used', False)

    @property
    def is_value_equipped(self):
        return self.value.get('is_equipped', False)

    @property
    def is_value_x(self, x):
        return self.value.get('is_' + x, False)


def is_none_valued_dict(d):
    return filter(lambda e: e is None, d.values())


def is_false_valued_dict(d):
    return len(filter(None, d.values())) != len(d)


def strip_if_unicode(e):
    return e.strip() if e and isinstance(e, unicode) else e


def is_weekend(d):
    assert isinstance(d, date) or isinstance(d, datetime)
    return d.weekday() in [e.weekday for e in [SA, SU]]


def next_work_day(dtstart=None, neglect_time=True):
    if not dtstart:
        dtstart = datetime.utcnow()
    if neglect_time:
        dtstart = datetime.combine(dtstart.date(), datetime.min.time())
    return list(rrule(DAILY, count=1, byweekday=(MO, TU, WE, TH, FR),
                      dtstart=dtstart))[0]


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


def limit_groups(query, model, partition_by, order_by, limit=None, offset=0):
    """Limits the number of rows returned for each group


    This utility allows you to apply a limit/offset to grouped rows of a query.
    Note that the query will only contain the data from `model`; i.e. you cannot
    add additional entities.

    :param query: The original query, including filters, joins, etc.
    :param model: The model class for `query`
    :param partition_by: The column to group by
    :param order_by: The column to order the partitions by
    :param limit: The maximum number of rows for each partition
    :param offset: The number of rows to skip in each partition
    """
    inner = query.add_columns(over(func.row_number(), partition_by=partition_by,
                                   order_by=order_by).label('rownum')).subquery()

    query = model.query.select_entity_from(inner)
    if limit:
        return query.filter(offset < inner.c.rownum, inner.c.rownum <= (limit + offset))
    else:
        return query.filter(offset < inner.c.rownum)


class Serializer(object):
    __public__ = []

    def to_serializable(self, attr='__public__', converters=None):
        j = {}
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
                    v = map(lambda e: e.to_serializable(), v)
                elif isinstance(v, dict):
                    v = dict((k, vv.to_serializable() if isinstance(vv, Serializer) else vv)
                             for k, vv in v.iteritems())
                if type(v) in converters:
                    v = converters[type(v)](v)
                j[name] = v
            except Exception:
                import traceback

                Logger.get('Serializer{}'.format(self.__class__.__name__)) \
                    .error(traceback.format_exc())
                raise IndicoError(
                    _('There was an error on the retrieval of {} of {}.')
                    .format(k, self.__class__.__name__.lower())
                )
        return j
