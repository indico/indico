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
import time
from datetime import datetime, timedelta

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import class_mapper

from MaKaC import user as user_mod
from MaKaC.accessControl import AdminList
from MaKaC.errors import MaKaCError
from MaKaC.plugins.base import PluginsHolder


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
    apply keyword arguments as filters

    func returns a class and an initial query on which
    filters will be applied by using class attributes

    eq   => ==
    ne   => !=
    ge   => >=
    gt   => >
    lt   => <
    le   => <=
    like => like
    in   => in_

    don't forget putting % for extra chars in both side
    it's not here to give flexibility to the caller
    """
    assert re.match(r'get\w+s', func.__name__)
    def add_filters(*args, **filters):
        cls, q = func(*args, **filters)
        for k, v in filters.iteritems():
            column = getattr(cls, k)

            if isinstance(v, tuple):
                requested_operator, value = v
            else:
                requested_operator, value = 'eq', v

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
        return q[:]  # to specify access than filtering
    return add_filters


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
            MaKaCError(_('accessChecked decorator expects '
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



def results_to_dict(results):
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


class Period:
    """
    Composed of two dates. Comparable by start date.
    """
    startDT = None
    endDT = None

    def __init__(self, start, end):
        self.start = start
        self.end = end

    def __cmp__(self, other):
        if not (self and other):
            return cmp(
                1 if self else None,
                1 if other else None
            )

        return cmp(self.start, other.start)

    def __hash__(self):
        return hash((self.start, self.end))

    def __repr__(self):
        return 'Period(%r, %r)' % (self.startDT, self.endDT)

    def __str__(self):
        return '{} -- {}'.format(self.start, self.end)


def intd(s, default=None):
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


def doesPeriodOverlap( *args, **kwargs ):
    """
    Returns true if periods do overlap. This requires both dates and times to overlap.
    Pass it either (period, period) or ( start1, end1, start2, end2 ).
    """
    if len( args ) == 4:
        return __doesPeriodOverlap( args[0], args[1], args[2], args[3] )
    if len( args ) == 2:
        return __doesPeriodOverlap( args[0].startDT, args[0].endDT, args[1].startDT, args[1].endDT )
    raise ValueError('2 or 4 arguments required: (period, period) or ( start1, end1, start2, end2 )')

def __doesPeriodOverlap( startDT1, endDT1, startDT2, endDT2 ):
    # Dates must overlap
    if endDT1.date() < startDT2.date() or endDT2.date() < startDT1.date():
        return False

    # Times must overlap
    if endDT1.time() <= startDT2.time() or endDT2.time() <= startDT1.time():
        return False
    return True

def overlap( *args, **kwargs ):
    """
    Returns two datetimes - the common part of two given periods.
    """
    if len( args ) == 4:
        return __overlap( args[0], args[1], args[2], args[3] )
    if len( args ) == 2:
        return __overlap( args[0].startDT, args[0].endDT, args[1].startDT, args[1].endDT )
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


def iterdays(first, last):
    """
    Iterate days between two dates:
    Example:
    for day in iterdays( datetime.now(), datetime.now() + timedelta( 21 ) ):
        pass
    """
    if not isinstance( first, datetime ): raise TypeError('pass datetime') #first = datetime( first.year, first.month, first.day )
    if not isinstance( last, datetime ): raise TypeError('pass datetime')  #last = datetime(  last.year, last.month, last.day )
    for day in range((last - first).days + 1):
        yield first + timedelta(day)

def weekNumber( dt ):
    """
    Lets assume dt is Friday.
    Then weekNumber( dt ) will return WHICH Friday of the month it is: 1st - 5th.
    """
    weekDay = dt.weekday()
    weekNumber = 0
    for day in iterdays( datetime( dt.year, dt.month, 1 ), dt ):
        if day.weekday() == weekDay:
            weekNumber += 1
    return weekNumber

class Impersistant( object ):

    def __init__( self, obj ):
        self.__obj = obj

    def getObject( self ):
        return self.__obj

def checkPresence( self, errors, attrName, type ):
    at = self.__dict__[attrName]
    if at == None:
        errors.append( attrName + ' is not present' )
        return
    #raise str( at.__class__.__name__ ) + " | " + str( at ) + " | " + str( type )
    if not isinstance( at, type ):
        errors.append( attrName + ' has invalid type' )
    return None

def toUTC( localNaiveDT ):
    """
    Converts naive (timezone-less) datetime to UTC.
    It assumes localNaiveDT to be in local/DTS timezone.
    """
    if localNaiveDT == None:
        return None
    if localNaiveDT.tzinfo != None:
        raise ValueError('This methods converts only _naive_ datetimes, assuming they are in local/DTS time. Naive datetimes does not contain information about timezone.')
    return localNaiveDT + timedelta( 0, time.altzone )


def fromUTC( utcNaiveDT ):
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
