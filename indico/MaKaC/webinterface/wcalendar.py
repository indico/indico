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

"""Contains the logic needed to build calendars  and overviews based on
    categories which can tell which conferences are happening between certain
    dates for a given set of categories
"""

import calendar
from collections import defaultdict
from BTrees.OOBTree import OOBTree
from datetime import timedelta
from dateutil.relativedelta import relativedelta

from MaKaC.errors import MaKaCError
from MaKaC.common import Locators, indexes
from MaKaC.conference import CategoryManager
from MaKaC.i18n import _
from flask import session
from pytz import timezone
from MaKaC.common.timezoneUtils import DisplayTZ
from indico.modules.events.timetable.util import get_category_timetable


def get_icons(detailed_data):
    icons = defaultdict(set)

    for __, day in detailed_data['events'].viewitems():
        for __, event in day:
            for categ_id in event.category_chain:
                if CategoryManager().getById(categ_id).getIcon():
                    icons[categ_id].add(event.id)
    return icons


class Day:

    def __init__(self, cal, day):
        self._calendar = cal
        self._day = day
        self._categories = set()
        for __, event in self._calendar._data['events'][self._day.date()]:
            for categ_id in event.category_chain:
                categ = CategoryManager().getById(categ_id)
                if categ in self._calendar._categList:
                    self._categories.add(categ)

    def _getCalendar( self ):
        return self._calendar

    def getConferences(self):
        return self._calendar._data['events'][self._day.date()]

    def getCategories(self):
        return list(self._categories)

    def getWeekDay( self ):
        return calendar.weekday( self._day.year, \
                                    self._day.month, \
                                    self._day.day )

    def getDayNumber( self ):
        return self._day.day

    def getDate( self ):
        return self._day


class Calendar:
    """This class represents a calendar which is a set of days which contain
        information about which conferences whithin certain categories are
        happening for each of these days and for a certain access. This class
        allows to configure the date interval and the category set to be
        considered and provides operations which allow to know about what's
        happening on each of those days.

       Attributes:
        _aw - (accessControl.AccessWrapper) Information about the access for
            which the calendar will be built.
        _sDate - (datetime) Starting date for the calendar.
        _eDate - (datetime) Ending date for the calendar.
        _categList - (List) List of categories to be considered.
        _days - (OOBTree) Index of days which build up the calendar.
    """

    def __init__( self, aw, sDate, eDate, categList=[] ):
        self._aw = aw
        self._tz = sDate.tzinfo
        self._sDate = sDate.replace(hour=0, minute=0, second=0, microsecond=0)
        self._eDate = eDate.replace(hour=23, minute=59, second=59, microsecond=0)
        self._categList = categList
        self._icons = {}
        self._days = {}
        self._data = self.getData()
        self._conf_categories = defaultdict(set)
        categ_id_list = {c.id for c in self._categList}

        for day, data in self._data['events'].viewitems():
            for __, event in data:
                for categ_id in event.category_chain:
                    if str(categ_id) in categ_id_list:
                        categ = CategoryManager().getById(str(categ_id))
                        self._conf_categories[event.id].add(categ)

    def getStartDate( self ):
        return self._sDate

    def getEndDate( self ):
        return self._eDate

    def getCategoryList( self ):
        return self._categList

    def getDay(self, day):
        return self._days.setdefault(day, Day(self, day))

    def getConferenceCategories(self, conf):
        return list(self._conf_categories[int(conf.getId())])

    def getLocator( self ):
        """Returns the generic locator for the current object. This locator
            contains the folloing entries corresponding to values for which
            the calendar is configured:
                selCateg -> List of category ids.
                sDate -> Starting date.
                eDate -> Ending date.
        """
        l = Locators.Locator()
        ids = []
        for c in self.getCategoryList():
            ids.append( c.getId() )
        l["selCateg"] = ids
        l["sDate"] = self.getStartDate().strftime("%Y-%m-%d")
        l["eDate"] = self.getStartDate().strftime("%Y-%m-%d")
        return l

    def getNormDate(self,date):
        # we have to normalize, but as we are going over all the days, we have to keep the date
        # and just normalize the tzinfo.
        norm_date=date.tzinfo.normalize(date)
        norm_date=norm_date.replace(year=date.year, month=date.month,day=date.day, hour=0)
        return norm_date

    def getDayList( self ):
        inc = timedelta( 1 )
        d = self.getStartDate()
        l = []
        while d<self.getEndDate():
            l.append( self.getDay( d ) )
            d += inc
        return l

    def __str__(self):
        l = []
        if self._days:
            for day in self._days.values():
                l.append("%s"%day)
        str =  _("Calendar between %s and %s: %s")%(\
                            self.getStartDate().strftime("%Y-%m-%d"), \
                            self.getEndDate().strftime("%Y-%m-%d"), \
                            "\n\t\t".join(l) )
        return str


class Month:
    def __init__( self, cal, date ):
        self._cal = cal
        self._date = date.replace(day=1)
        self._month = int( date.month )
        self._year = int( date.year )

    def getMonthNumber( self ):
        return self._month

    def getYear( self ):
        return self._year

    def getCalendar( self ):
        return self._cal

    def getDayList( self ):
        inc = timedelta(1)
        sd = self._date
        l = []
        while sd.month == self.getMonthNumber():
            l.append( self.getCalendar().getDay( sd ) )
            sd += inc
        return l


class MonthCalendar( Calendar ):

    def __init__( self, aw, sDate, nrMonths, nrColumns, categList=[] ):
        self._nrMonths = int(nrMonths)
        self._nrColumns = int(nrColumns)
        sd = sDate.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        ed = sd + timedelta( 30*self._nrMonths )
        Calendar.__init__( self, aw, sd, ed, categList )
        self._data = self.getData()

    def getLocator( self ):
        l = Locators.Locator()
        ids = []
        for c in self.getCategoryList():
            ids.append( c.getId() )
        l["selCateg"] = ids
        l["sDate"] = self.getStartDate().strftime("%Y-%m-%d")
        l["months"] = self._nrMonths
        return l

    def getNrMonths( self ):
        return self._nrMonths

    def getNrColumns( self ):
        return self._nrColumns

    def getMonthList( self ):
        inc = timedelta(31)
        sd = self.getStartDate()
        l = []
        while sd < self.getEndDate():
            l.append( Month( self, sd))
            sd += inc
        return l

    def getData(self):
        categ_ids = tuple(int(cat.id) for cat in self._categList)
        tz = timezone(DisplayTZ(session.user, None, useServerTZ=True).getDisplayTZ())
        self._data = get_category_timetable(categ_ids,
                                            self.getStartDate(),
                                            self.getEndDate() + timedelta(days=1) - timedelta(seconds=1),
                                            detail_level='event',
                                            tz=tz,
                                            from_categ=self._categList[0])
        return self._data

class Overview:
    _allowedDetailLevels = ("conference", "session", "contribution")

    def __init__( self, aw, date, categList=[] ):
        self._detailLevel = "conference"
        self._categList = categList
        self._date = date
        self._aw = aw
        self._cal = None

    def getIcons(self):
        return get_icons(self._data)

    def getLocator( self ):
        l = Locators.Locator()
        ids = []
        for c in self.getCategoryList():
            ids.append( c.getId() )
        l["selCateg"] = ids
        l["detail"] = self.getDetailLevel()
        l["day"] = self.getDate().day
        l["month"] = self.getDate().month
        l["year"] = self.getDate().year
        l["period"] = "day"
        return l

    def getDetailLevel( self ):
        return self._detailLevel

    def setDetailLevel( self, newDL ):
        newDL = newDL.strip().lower()
        if not (newDL in self.getAllowedDetailLevels()):
            raise MaKaCError( _("imposible to set this detail level"))
        self._detailLevel = newDL

    def getAllowedDetailLevels( self ):
        return self._allowedDetailLevels

    def getCategoryList( self ):
        return self._categList

    def getDate( self ):
        return self._date

    def getStartDate( self ):
        return self.getDate()

    def getEndDate( self ):
        return self.getDate()

    def getData(self):
        categ_ids = tuple(int(cat.id) for cat in self._categList)
        tz = timezone(DisplayTZ(session.user, None, useServerTZ=True).getDisplayTZ())
        self._data = get_category_timetable(categ_ids,
                                            self.getStartDate(),
                                            self.getEndDate() + timedelta(days=1) - timedelta(seconds=1),
                                            detail_level=self.getDetailLevel(),
                                            tz=tz,
                                            from_categ=self._categList[0])
        return self._data

    def getDayList( self ):
        if not self._cal:
            self._cal = MonthCalendar(self._aw, self.getStartDate(),
                                      1, 3, self.getCategoryList())
        return self._cal.getDayList()

    def getAW( self ):
        return self._aw

    def getOverviewNextPeriod(self):
        """Returns an exact copy of the current overview object for the next
            day"""
        ow = Overview(self.getAW(),
                      self.getDate() + relativedelta(days=1),
                      self.getCategoryList())
        ow.setDetailLevel(self.getDetailLevel())
        return ow

    def getOverviewPrevPeriod(self):
        """Returns an exact copy of the current overview object for the previous
            day"""
        ow = Overview(self.getAW(),
                      self.getDate() - relativedelta(days=1),
                      self.getCategoryList())
        ow.setDetailLevel(self.getDetailLevel())
        return ow

    def getOverviewNextBigPeriod(self):
        """Returns an exact copy of the current overview object for the next
            day"""
        d = self.getDate()
        ow = Overview(self.getAW(),
                      d - relativedelta(months=1),
                      self.getCategoryList())
        ow.setDetailLevel(self.getDetailLevel())
        return ow

    def getOverviewPrevBigPeriod(self):
        """Returns an exact copy of the current overview object for the previous
            day"""
        d = self.getDate()
        ow = Overview(self.getAW(),
                      d + relativedelta(months=1),
                      self.getCategoryList())
        ow.setDetailLevel(self.getDetailLevel())
        return ow

    def getOverviewOtherCateg( self, categid ):
        """Returns an exact copy of the current overview object for another
            category"""
        ow = Overview( self.getAW(), \
                        self.getDate(), \
                        [categid] )
        ow.setDetailLevel( self.getDetailLevel() )
        return ow



class WeekOverview( Overview ):

    def getLocator( self ):
        l = Overview.getLocator( self )
        l["period"] = "week"
        return l

    def getStartDate( self ):
        d = self.getDate()
        inc = timedelta( calendar.weekday( d.year, d.month, d.day ) )
        return d-inc

    def getEndDate( self ):
        d = self.getDate()
        inc = timedelta( 6 - calendar.weekday( d.year, d.month, d.day ) )
        return d+inc

    def getOverviewNextPeriod(self):
        """Returns an exact copy of the current overview object for the next
            week"""
        ow = WeekOverview(self.getAW(),
                          self.getDate() + relativedelta(weeks=1),
                          self.getCategoryList())
        ow.setDetailLevel(self.getDetailLevel())
        return ow

    def getOverviewPrevPeriod(self):
        """Returns an exact copy of the current overview object for the previous
            week"""
        ow = WeekOverview(self.getAW(),
                          self.getDate() - relativedelta(weeks=1),
                          self.getCategoryList())
        ow.setDetailLevel(self.getDetailLevel())
        return ow

    def getOverviewOtherCateg( self, categid ):
        """Returns an exact copy of the current overview object for another
            category"""
        ow = WeekOverview( self.getAW(), \
                        self.getDate(), \
                        [categid] )
        ow.setDetailLevel( self.getDetailLevel() )
        return ow


class MonthOverview( Overview ):

    def getLocator( self ):
        l = Overview.getLocator( self )
        l["period"] = "month"
        return l

    def getStartDate( self ):
        d = self.getDate()
        return d.replace(day=1)

    def getEndDate( self ):
        try:
            d = self.getStartDate().replace(month=self.getDate().month+1) - timedelta(1)
        except:
            d = self.getStartDate().replace(year=self.getDate().year+1,month=1) - timedelta(1)
        return d

    def getOverviewNextPeriod(self):
        """Returns an exact copy of the current overview object for the next
            month"""
        ow = MonthOverview(self.getAW(),
                           self.getDate() + relativedelta(months=1),
                           self.getCategoryList())
        ow.setDetailLevel(self.getDetailLevel())
        return ow

    def getOverviewPrevPeriod(self):
        """Returns an exact copy of the current overview object for the previous
            month"""
        ow = MonthOverview(self.getAW(),
                           self.getDate() - relativedelta(months=1),
                           self.getCategoryList())
        ow.setDetailLevel(self.getDetailLevel())
        return ow

    def getOverviewNextBigPeriod(self):
        """Returns an exact copy of the current overview object for the next
            day"""
        d = self.getDate()
        ow = MonthOverview(self.getAW(),
                           d + relativedelta(years=1),
                           self.getCategoryList())
        ow.setDetailLevel(self.getDetailLevel())
        return ow

    def getOverviewPrevBigPeriod(self):
        """Returns an exact copy of the current overview object for the previous
            day"""
        d = self.getDate()
        ow = MonthOverview(self.getAW(),
                           d - relativedelta(years=1),
                           self.getCategoryList())
        ow.setDetailLevel(self.getDetailLevel())
        return ow

    def getOverviewOtherCateg( self, categid ):
        """Returns an exact copy of the current overview object for another
            category"""
        ow = MonthOverview( self.getAW(), \
                        self.getDate(), \
                        [categid] )
        ow.setDetailLevel( self.getDetailLevel() )
        return ow
