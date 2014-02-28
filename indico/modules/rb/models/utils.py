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
import re
import string
import struct
import time
from datetime import date, datetime, timedelta
from dateutil.relativedelta import MO, TU, WE, TH, FR, SA, SU
from dateutil.rrule import rrule, DAILY
from functools import wraps
from random import randrange

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import class_mapper

from MaKaC import user as user_mod
from MaKaC.accessControl import AdminList
from MaKaC.plugins.base import PluginsHolder

from indico.core.errors import IndicoError
from indico.core.logger import Logger
from indico.util.i18n import _
from indico.util.json import dumps


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


def apply_filters(q, entity, **filters):
    """
    for a given start query `q`, given filters are applied onto query

    query mapping:
        eq   => ==
        ne   => !=
        ge   => >=
        gt   => >
        lt   => <
        le   => <=
        like => like
        in   => in_

        `%` must be explicitly given for `like` filter
    """

    for column_name, condition in filters.items():
        column = getattr(entity, column_name)

        # assume equal unless operator is specified
        if isinstance(condition, tuple):
            requested_operator, value = condition
        else:
            requested_operator, value = 'eq', condition

        try:
            mapped_operator = filter(
                lambda possible_attr: hasattr(
                    column,
                    possible_attr % requested_operator
                ),
                ['%s', '%s_', '__%s__']
            )[0] % requested_operator
        except IndexError:
            raise RuntimeError('Invalid filter operator')

        q = q.filter(getattr(column, mapped_operator)(value))
    return q


def filtered(func):
    """
    apply filters and returns all objects
    """
    assert re.match(r'filter\w+s', func.__name__)
    def add_filters(*args, **filters):
        cls, q = func(*args, **filters)
        return apply_filters(q, cls, **filters).all()
    return add_filters


def unimplemented(exceptions=(Exception,), message='Unimplemented'):
    def _unimplemented(func):
        @wraps(func)
        def _wrapper(*args, **kw):
            try:
                return func(*args, **kw)
            except exceptions:
                raise IndicoError(message)
        return _wrapper
    return _unimplemented


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
            IndicoError(_('accessChecked decorator expects '
                          'an avatar as a positional argument'))

        if AdminList.getInstance().isAdmin(avatar):
            return True
        else:
            def isAuthorized(entity):
                if isinstance(entity, user_mod.Group):
                    return entity.containsUser(avatar)
                elif isinstance(entity, avatar):
                    return entity == avatar
                else:
                    raise RuntimeError('Unexpected entity type')

            authorized_list = (PluginsHolder().getPluginType("RoomBooking")
                                              .getOption("AuthorisedUsersGroups")
                                              .getValue())
            if authorized_list:
                return any(map(isAuthorized, authorized_list))
            else:
                return True

    def check_access(*args, **kwargs):
        if not check_access_internal(*args, **kwargs):
            return False
        return func(*args, **kwargs)
    return check_access


def add_to_session():
    """
    Automatically add modified objects to session
    """
    pass


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
        'archivalValid': 0,
        'archivalCancelled': 0,
        'archivalRejected': 0
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


class RBFormatter:

    @staticmethod
    def formatString(s, entity):
        """
        Parse format string and return formatted string
        where arguments are retrieved from given entity i.e room
        """
        return s.format(
            **dict((k, getattr(entity, k))
                   for _, k, _, _ in string.Formatter().parse(s) if k)
        )

    @staticmethod
    def formatDate(d):
        """Convert the date to the Indico "de facto" standard"""
        return d.strftime("%a %d/%m/%Y")

    @staticmethod
    def formatDateTime(dt):
        """Convert the date to the Indico "de facto" standard"""
        return dt.strftime("%a %d/%m/%Y %H:%M")


class JSONStringBridgeMixin:
    """
    A hybrid property to encode/decode automatically
    a string column to JSON and vice versa.

    Assumes mapped column name is 'raw_data'
    """

    @hybrid_property
    def value(self):
        return json.loads(self.raw_data)

    @value.setter
    def value(self, data):
        self.raw_data = json.dumps(data)

    @hybrid_property
    def is_value_required(self):
        return self.value.get('is_required', False)

    @hybrid_property
    def is_value_hidden(self):
        return self.value.get('is_hidden', False)

    @hybrid_property
    def is_value_used(self):
        return self.value.get('is_used', False)

    @hybrid_property
    def is_value_equipped(self):
        return self.value.get('is_equipped', False)

    @hybrid_property
    def is_value_x(self, x):
        return self.value.get('is_' + x, False)


def requiresDateOrDatetime(func):
    def is_date_or_datetime(d):
        return isinstance(d, date) or isinstance(d, datetime)

    def _wrapper(*args, **kw):
        if all(map(is_date_or_datetime, args)) and all(map(is_date_or_datetime, kw.values())):
            return func(*args, **kw)
        raise IndicoError(_(''))
    return _wrapper


def is_none_valued_dict(d):
    return filter(lambda e: e is None, d.values())


def is_false_valued_dict(d):
    return len(filter(None, d.values())) != len(d)


def sifu(e):
    return e.strip() if e and isinstance(e, unicode) else e
strip_if_unicode = sifu


def get_checked_param_dict(f, params, converter=unicode):
    return dict((k, strip_if_unicode(f.get(k, type=converter))) for k in params)


def iterdays(start, end):
    """
    Iterate days between two dates:
    Example:
    for day in iterdays(datetime.now(), datetime.now() + timedelta(21)):
        pass
    """
    for day in range((end - start).days + 1):
        yield start + timedelta(day)


def iterdaysByUtil(start, end):
    return rrule(DAILY, dtstart=start, until=end)


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


def next_day_skip_if_weekend(dtstart=None):
    if not dtstart:
        dtstart = datetime.utcnow()
    dtstart += timedelta(1)
    return next_work_day(dtstart=dtstart, neglect_time=False)


def getWeekNumber(dt):
    """
    Lets assume dt is Friday.
    Then weekNumber(dt) will return WHICH Friday of the month it is: 1st - 5th.
    """
    weekDay, weekNumber = dt.weekday(), 0
    for day in iterdays(date(dt.year, dt.month, 1), dt):
        if day.weekday() == weekDay:
            weekNumber += 1
    return weekNumber


def getTimeDiff(start, end):
    diff = datetime.combine(date.today(), end) - datetime.combine(date.today(), start)
    return diff.total_seconds()


def getRandomDatetime(start, end):
    """
    Returns a random datetime between two datetime objects.
    """
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = randrange(int_delta)
    return start + timedelta(seconds=random_second)


def getRandomDate(start, end):
    """
    Returns a random date between two date objects.
    """
    r = getRandomDatetime(start, end)
    return r.date() if isinstance(r, datetime) else r


def isShortInt(n):
    try:
        struct.pack('H', n)  # i.e. 0 <= n < (1 << 16)
        return True
    except:
        return False


def intOrDefault(s, default=None):
    """
    Like int() but returns default value if conversion failed.
    """
    try:
        return int(s)
    except:
        return default


def qbeMatch( example, candidate, special, **kwargs ):
    """
    Queary By Example Match.

    Used for "query by example" searching mechanism. The 'example'
    parameter defines match conditions. Function returns true if
    'candidate' matches 'example', false otherwise.

    The rules for generic comparison:
    - Only not-None attributes of 'example' are compared.
    - Strings are matched by inclusion, not equality.

    Arguments:
    example - specifies match conditions. If example.attribute is
        None, the attribute is skipped as not important.
    candidate - object that is testet for match with example
    special - method that knows how to treat special attributes.
        Use it to customize comparison of choosen attributes.
        It is passed attrName, attrVal1, attrVal2, **kwargs
        It is expected to return:
        - None if attrName is not special. Then standard comparison will be
          performed
        - True if values are equal
        - False otherwise
    """

    for attrName in dir( example ):
        # Skip methods, private attributes and Nones
        if attrName[0] == '_' or attrName in ['avaibleVC', 'vcList', 'needsAVCSetup', 'verboseEquipment',
                                              'resvStartNotification', 'resvEndNotification', 'resvNotificationAssistance', 'maxAdvanceDays']:
            continue

        exAttrVal = getattr(example, attrName)
        attrType = exAttrVal.__class__.__name__

        if attrType in ('instancemethod', 'staticmethod', 'function') or exAttrVal == None:
            continue

        candAttrVal = getattr(candidate, attrName)
        if candAttrVal == None           and attrName not in ['repeatability', 'weekDay', 'weekNumber']: # Ugly hack :/
            return False # because exAttrVal != None

        # Special comparison for some attributes
        areEqual = special( attrName, exAttrVal, candAttrVal, **kwargs )

        # Generic comparison
        if areEqual == None:
            if attrType in ('int', 'float', 'bool', 'datetime' ):
                # Exact match
                areEqual = ( candAttrVal == exAttrVal )
            elif attrType == 'str':
                areEqual = candAttrVal.lower() == exAttrVal.lower()
            else:
                raise attrType + ": " + str( candAttrVal ) + " - can not compare"

        if not areEqual:
            #print "Does not match: %s (%s : %s)" % (attrName, str( exAttrVal ), str( attrVal ) )
            return False
#        if 'Room' not in example.__class__.__name__ and attrName == 'repeatability' and example.repeatability == 1 and candidate.reason == "TDAQ Meeting" and candidate.startDT == datetime( 2007, 05, 21, 9 ):
#            raise str( areEqual ) + '--' + str( example )

    # All attributes match
    return True


def containsExactly_OR_containsAny( attrValExample, attrValCandidate ):
    attrValExample = attrValExample.strip().lower()
    attrValCandidate = attrValCandidate.lower()

    if attrValExample[0] in ['"', "'"] and attrValExample[-1] in ['"', "'"]:
        # If quoted, check for exact containmet
        attrValExample = attrValExample[1:-1]
        return attrValExample in attrValCandidate
    else:
        # Else, check for containment of any word
        words = attrValExample.split()
        for word in words:
            if word in attrValCandidate:
                return True

    return False

def get_overlap(st1, et1, st2, et2):
    st, et = max(st1, st2), min(et1, et2)
    if st <= et:
        return st, et


def doesPeriodOverlap(*args):
    """
    Returns true if periods do overlap. This requires both dates and times to overlap.
    Pass it either (period, period) or ( start1, end1, start2, end2 ).
    """
    largs = len(args)
    if largs == 4:
        return __doesPeriodOverlap(*args)
    if largs == 2:
        return __doesPeriodOverlap(args[0].startDT, args[0].endDT, args[1].startDT, args[1].endDT)
    raise ValueError('2 or 4 arguments required: (period, period) or ( start1, end1, start2, end2 )')

def __doesPeriodOverlap(startDT1, endDT1, startDT2, endDT2):
    # Dates must overlap
    if endDT1.date() < startDT2.date() or endDT2.date() < startDT1.date():
        return False

    # Times must overlap
    if endDT1.time() <= startDT2.time() or endDT2.time() <= startDT1.time():
        return False
    return True

def overlap(*args, **kwargs):
    """
    Returns two datetimes - the common part of two given periods.
    """
    if len( args ) == 4:
        return __overlap(args[0], args[1], args[2], args[3])
    if len( args ) == 2:
        return __overlap(args[0].startDT, args[0].endDT, args[1].startDT, args[1].endDT)
    raise ValueError('2 or 4 arguments required: (period, period) or ( start1, end1, start2, end2 )')


def __overlap( startDT1, endDT1, startDT2, endDT2):
    if not doesPeriodOverlap( startDT1, endDT1, startDT2, endDT2):
        # [---]  [----]
        return None

    dates = __overlapDates( startDT1.date(), endDT1.date(), startDT2.date(), endDT2.date() )
    times = __overlapTimes( startDT1.time(), endDT1.time(), startDT2.time(), endDT2.time() )

    fromOverlap = datetime( dates[0].year, dates[0].month, dates[0].day, times[0].hour, times[0].minute, times[0].second )
    toOverlap = datetime( dates[1].year, dates[1].month, dates[1].day, times[1].hour, times[1].minute, times[1].second )

    return ( fromOverlap, toOverlap )

def __overlapDates( startD1, endD1, startD2, endD2 ):

    if endD1 >= startD2 and endD1 <= endD2 and startD1 <= startD2:
        # [-----]       (1)
        #     [------]  (2)
        return ( startD2, endD1 )

    if startD1 >= startD2 and endD1 <= endD2:
        #    [---]      (1)
        # [----------]  (2)
        return ( startD1, endD1 )

    return __overlapDates( startD2, endD2, startD1, endD1 )

def __overlapTimes( startT1, endT1, startT2, endT2 ):

    if endT1 >= startT2 and endT1 <= endT2 and startT1 <= startT2:
        # [-----]       (1)
        #     [------]  (2)
        return ( startT2, endT1 )

    if startT1 >= startT2 and endT1 <= endT2:
        #    [---]      (1)
        # [----------]  (2)
        return ( startT1, endT1 )

    return __overlapTimes( startT2, endT2, startT1, endT1 )


class Impersistant(object):

    def __init__(self, obj):
        self.__obj = obj

    def getObject(self):
        return self.__obj

def checkPresence(self, errors, attrName, type):
    at = self.__dict__[attrName]
    if at == None:
        errors.append( attrName + ' is not present' )
        return
    #raise str( at.__class__.__name__ ) + " | " + str( at ) + " | " + str( type )
    if not isinstance( at, type ):
        errors.append( attrName + ' has invalid type' )
    return None

def toUTC(localNaiveDT):
    """
    Converts naive (timezone-less) datetime to UTC.
    It assumes localNaiveDT to be in local/DTS timezone.
    """
    if localNaiveDT == None:
        return None
    if localNaiveDT.tzinfo != None:
        raise ValueError('This methods converts only _naive_ datetimes, assuming they are in local/DTS time. Naive datetimes does not contain information about timezone.')
    return localNaiveDT + timedelta( 0, time.altzone )


def fromUTC(utcNaiveDT):
    #if utcNaiveDT == None:
    #    return None
    try:
        if utcNaiveDT.tzinfo != None:
            raise ValueError('This methods converts only _naive_ datetimes, assuming they are in UTC time. Naive datetimes does not contain information about timezone.')
        return utcNaiveDT - timedelta( 0, time.altzone )
    except AttributeError:
        return None


def datespan(startDate, endDate, delta=timedelta(days=1)):
    currentDate = startDate
    while currentDate <= endDate:
        yield currentDate
        currentDate += delta


def dateAdvanceAllowed(date, days):
    from MaKaC.common.timezoneUtils import nowutc, dayDifference, naive2local
    import MaKaC.common.info as info
    tz = info.HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()
    return dayDifference(naive2local(date, tz), nowutc(), tz) > days


class Serializer(object):
    __public__ = []

    def to_serializable(self, attr='__public__'):
        j = {}
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
                j[name] = v
            except Exception:
                import traceback
                Logger.get('Serializer{}'.format(self.__class__.__name__))\
                      .error(traceback.format_exc())
                raise IndicoError(
                    _('There was an error on the retrieval of {} of {}.')
                    .format(k, self.__class__.__name__.lower())
                )
        return j
# ============================================================================
# ================================== TEST ====================================
# ============================================================================

class Test:

    @staticmethod
    def doesPeriodOverlap():

        # Days overlap, hours not
        ret = doesPeriodOverlap(
            datetime( 2006, 9, 20, 16 ),
            datetime( 2006, 9, 20, 18 ),
            datetime( 2006, 9, 20, 18, 30 ),
            datetime( 2006, 9, 20, 19 ) )
        assert( not ret )

        ret = doesPeriodOverlap(
            datetime( 2006, 9, 20, 16 ),
            datetime( 2006, 9, 25, 18 ),
            datetime( 2006, 9, 23, 13 ),
            datetime( 2006, 9, 24, 15 ) )
        assert( not ret )

        # Days does not overlap, hours do
        ret = doesPeriodOverlap(
            datetime( 2006, 9, 20, 16 ),
            datetime( 2006, 9, 20, 18 ),
            datetime( 2006, 9, 21, 16, 30 ),
            datetime( 2006, 9, 22, 17, ) )
        assert( not ret )

        p1 = Period( datetime( 2006, 12, 1, 8 ), datetime( 2006, 12, 1, 9 ) )
        p2 = Period( datetime( 2006, 12, 1, 9 ), datetime( 2006, 12, 1, 10 ) )
        assert( not doesPeriodOverlap( p1, p2 ) )

        # Periods overlap
        ret = doesPeriodOverlap(
            datetime( 2006, 9, 20, 16 ),
            datetime( 2006, 9, 25, 18 ),
            datetime( 2006, 9, 23, 13 ),
            datetime( 2006, 9, 24, 17 ) )
        assert( ret )

    @staticmethod
    def overlap():

        # Days overlap, hours not
        ret = overlap(
            datetime( 2006, 9, 20, 16 ),
            datetime( 2006, 9, 20, 18 ),
            datetime( 2006, 9, 20, 18, 30 ),
            datetime( 2006, 9, 20, 19 ) )
        assert( ret == None )

        # Periods overlap
        sdt, edt = overlap(
            datetime( 2006, 9, 20, 16 ),
            datetime( 2006, 9, 25, 18 ),
            datetime( 2006, 9, 23, 13 ),
            datetime( 2006, 9, 24, 17 ) )
        print sdt, edt


if __name__ == "__main__":
    Test.doesPeriodOverlap()
    Test.overlap()
