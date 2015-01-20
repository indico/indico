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

"""Contains the logic needed to build calendars  and overviews based on
    categories which can tell which conferences are happening between certain
    dates for a given set of categories
"""

import calendar

from BTrees.OOBTree import OOBTree
from datetime import timedelta,datetime

import MaKaC.conference as conference
from MaKaC.errors import MaKaCError
from MaKaC.common import Locators,indexes
from indico.core.config import Config
from MaKaC.conference import CategoryManager
from MaKaC.conference import Category
from MaKaC.i18n import _
from pytz import timezone
from MaKaC.common.timezoneUtils import DisplayTZ,nowutc

class Day:

    def __init__( self, cal, day ):
        self._calendar = cal
        self._day = day
        self._confs = OOBTree()
        self._categs = []

    def _getCalendar( self ):
        return self._calendar

    def addConference(self,conf,categList,tz):
        for categ in categList:
            if categ not in self._categs:
                self._categs.append(categ)
        t = conf.getStartDate().astimezone(tz).time()
        if not self._confs.has_key(t):
            self._confs[t]=set()
        self._confs[t].add(conf)

    #sorting functions that caches calculated start times for every conf
    def _sortFunc(self, x,y):
        return cmp(self._cache[x], self._cache[y])

    def _calculateCache(self, confs):
        self._cache = {}
        for conf in confs:
            self._cache[conf] = conf.calculateDayStartTime(self._day).time()

    def getConferences(self):
        return [conf for confs in self._confs.values() for conf in confs]

    def getConferencesWithStartTime(self):
        res= [conf for confs in self._confs.values() for conf in confs]
        self._calculateCache(res)
        if res!=[]:
            res.sort(self._sortFunc)
        return [(event, self._cache[event]) for event in res]

    def getCategories(self):
        return self._categs

    def getWeekDay( self ):
        return calendar.weekday( self._day.year, \
                                    self._day.month, \
                                    self._day.day )

    def getDayNumber( self ):
        return self._day.day

    def getDate( self ):
        return self._day

    def __str__( self ):
        return "CalendarDay at '%s': %s --> %s"%(self._day, self._confs, self._categs)


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
        self._days = None

    def getIcons( self ):
        try:
            return self._icons
        except:
            self._icons = {}
            return {}

    def setIcons(self, categ):
        """Retrieves the list of icons in a given category tree
        """
        if categ.getIcon() != None:
            return [categ.getId()]
        res = []
        for subcat in categ.getSubCategoryList():
            res += self.setIcons(subcat)
        return res

    def getStartDate( self ):
        return self._sDate

    def getEndDate( self ):
        return self._eDate

    def getCategoryList( self ):
        return self._categList

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

    def _mapConferenceToDays(self,conf,categList):
        """Registers a given conference for the days on which it is taking place
            whithin the calendar date interval.

           Parameters:
            conf - (conference.Conference) Conference to be mapped.
            categList - (List) List of calendar categories in which the
                specified conference is found.
        """

        inc = timedelta(1)
        d = max(conf.getStartDate().astimezone(self._tz).replace(hour=0,minute=0,second=0),
                self.getStartDate().astimezone(self._tz).replace(hour=0,minute=0,second=0))
        ed = min(conf.getEndDate().astimezone(self._tz), self.getEndDate().astimezone(self._tz))
        if ed > self.getEndDate():
            ed = self.getEndDate()

        while d <= ed:
            #norm_date=d.tzinfo.normalize(d)
            #norm_date=norm_date.replace(hour=0)
            norm_date=self.getNormDate(d)
            if not self._days.has_key( norm_date ):
                self._days[norm_date] = Day( self, d )

            self._days[norm_date].addConference( conf, categList, self._tz )
            d += inc

    def _initialiseDays( self ):
        """
        """
        self._days = OOBTree()
        res = set()
        self._categIdx = {}
        self._icons={}
        catDayIdx = indexes.IndexesHolder().getIndex("categoryDate")
        for categ in self.getCategoryList():
            confs = catDayIdx.getObjectsInDays(categ.getId(), self.getStartDate(), self.getEndDate())
            for conf in confs:
                confId = conf.getId()
                if not self._categIdx.has_key(confId):
                    self._categIdx[confId]=[]
                self._categIdx[confId].append(categ)
            res.update(confs)
        for conf in res:
            #getting icon from the nearest owner category
            owner = conf.getOwner()
            while owner != None and owner.getId() != "0":
                if owner.getIcon():
                    if self._icons.has_key(owner.getId()):
                        self._icons[owner.getId()].append(conf.getId())
                    else:
                        self._icons[owner.getId()] = [conf.getId()]
                    break
                owner = owner.getOwner()
            #mapping conf to days
            self._mapConferenceToDays(conf ,self._categIdx[conf.getId()])



    def getNormDate(self,date):
        # we have to normalize, but as we are going over all the days, we have to keep the date
        # and just normalize the tzinfo.
        norm_date=date.tzinfo.normalize(date)
        norm_date=norm_date.replace(year=date.year, month=date.month,day=date.day, hour=0)
        return norm_date

    def getDay( self, date ):
        if not self._days:
            self._initialiseDays()
        norm_date=self.getNormDate(date)
        if not self._days.has_key( norm_date ):
            self._days[norm_date] = Day( self, date )
        return self._days[norm_date]

    def getDayList( self ):
        inc = timedelta( 1 )
        d = self.getStartDate()
        l = []
        while d<self.getEndDate():
            l.append( self.getDay( d ) )
            d += inc
        return l

    def getConferenceCategories( self, conf ):
        return self._categIdx[conf.getId()]

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
    def getNames():
        return [ _("January"),  _("February"),  _("March"),  _("April"),  _("May"),  _("June"),  _("July"), _("August"),  _("September"),  _("October"),  _("November"),  _("December") ]
    getNames = staticmethod(getNames)

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

    def getName( self ):
        return self.getNames()[self._month-1]

    def getDayList( self ):
        inc = timedelta(1)
        sd = self._date
        l = []
        while sd.month == self.getMonthNumber():
            l.append( self.getCalendar().getDay( sd ) )
            sd += inc
        return l

    def __str__( self ):
        l = []
        for day in self.getDayList():
                l.append("%s"%(day))
        str =  _("Month '%s %s':%s")%(\
                            self.getName(), \
                            self.getYear(), \
                            "\n\t\t".join(l) )
        return str


class MonthCalendar( Calendar ):

    def __init__( self, aw, sDate, nrMonths, nrColumns, categList=[] ):
        self._nrMonths = int(nrMonths)
        self._nrColumns = int(nrColumns)
        sd = sDate.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        ed = sd + timedelta( 30*self._nrMonths )
        Calendar.__init__( self, aw, sd, ed, categList )

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


class Overview:
    _allowedDetailLevels = ("conference", "session", "contribution")

    def __init__( self, aw, date, categList=[] ):
        self._detailLevel = "conference"
        self._categList = categList
        self._date = date
        self._aw = aw
        self._cal = None

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

    def getConferencesWithStartTime( self, date=None ):
        if not self._cal:
            self._cal = Calendar( self._aw, self.getStartDate(), \
                                    self.getEndDate(), self.getCategoryList() )
        if not date:
            date = self.getDate()
        return self._cal.getDay( date ).getConferencesWithStartTime()

    def getDayList( self ):
        if not self._cal:
            self._cal = Calendar( self._aw, self.getStartDate(), \
                                    self.getEndDate(), self.getCategoryList() )
        return self._cal.getDayList()

    def getAW( self ):
        return self._aw

    def getOverviewNextPeriod( self ):
        """Returns an exact copy of the current overview object for the next
            day"""
        ow = Overview( self.getAW(), \
                        self.getDate()+timedelta(1), \
                        self.getCategoryList() )
        ow.setDetailLevel( self.getDetailLevel() )
        return ow

    def getOverviewPrevPeriod( self ):
        """Returns an exact copy of the current overview object for the previous
            day"""
        ow = Overview( self.getAW(), \
                        self.getDate()-timedelta(1), \
                        self.getCategoryList() )
        ow.setDetailLevel( self.getDetailLevel() )
        return ow

    def getOverviewNextBigPeriod( self ):
        """Returns an exact copy of the current overview object for the next
            day"""
        d = self.getDate()
        month = d.month
        year = d.year
        if month == 12:
            nextmonth = 1
            nextyear = year + 1
        else:
            nextmonth = month + 1
            nextyear = year
        day = d.day
        while True:
            try:
                d = d.replace(year=nextyear,month=nextmonth,day=day)
                break
            except:
                day = day-1
        ow = Overview( self.getAW(), \
                        d, \
                        self.getCategoryList() )
        ow.setDetailLevel( self.getDetailLevel() )
        return ow

    def getOverviewPrevBigPeriod( self ):
        """Returns an exact copy of the current overview object for the previous
            day"""
        d = self.getDate()
        month = d.month
        year = d.year
        if month == 1:
            prevmonth = 12
            prevyear = year -1
        else:
            prevmonth = month - 1
            prevyear = year
        day = d.day
        while True:
            try:
                d = d.replace(year=prevyear,month=prevmonth,day=day)
                break
            except:
                day = day-1
        ow = Overview( self.getAW(), \
                        d, \
                        self.getCategoryList() )
        ow.setDetailLevel( self.getDetailLevel() )
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

    def getOverviewNextPeriod( self ):
        """Returns an exact copy of the current overview object for the next
            week"""
        ow = WeekOverview( self.getAW(), \
                        self.getDate()+timedelta(7), \
                        self.getCategoryList() )
        ow.setDetailLevel( self.getDetailLevel() )
        return ow

    def getOverviewPrevPeriod( self ):
        """Returns an exact copy of the current overview object for the previous
            week"""
        ow = WeekOverview( self.getAW(), \
                        self.getDate()-timedelta(7), \
                        self.getCategoryList() )
        ow.setDetailLevel( self.getDetailLevel() )
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

    def getOverviewNextPeriod( self ):
        """Returns an exact copy of the current overview object for the next
            month"""
        ow  = MonthOverview( self.getAW(), \
                        self.getDate()+timedelta(30), \
                        self.getCategoryList() )
        ow.setDetailLevel( self.getDetailLevel() )
        return ow

    def getOverviewPrevPeriod( self ):
        """Returns an exact copy of the current overview object for the previous
            month"""
        ow = MonthOverview( self.getAW(), \
                        self.getDate()-timedelta(30), \
                        self.getCategoryList() )
        ow.setDetailLevel( self.getDetailLevel() )
        return ow

    def getOverviewNextBigPeriod( self ):
        """Returns an exact copy of the current overview object for the next
            day"""
        d = self.getDate().replace(year=self.getDate().year+1)
        ow = MonthOverview( self.getAW(), \
                        d, \
                        self.getCategoryList() )
        ow.setDetailLevel( self.getDetailLevel() )
        return ow

    def getOverviewPrevBigPeriod( self ):
        """Returns an exact copy of the current overview object for the previous
            day"""
        d = self.getDate().replace(year=self.getDate().year-1)
        ow = MonthOverview( self.getAW(), \
                        d, \
                        self.getCategoryList() )
        ow.setDetailLevel( self.getDetailLevel() )
        return ow

    def getOverviewOtherCateg( self, categid ):
        """Returns an exact copy of the current overview object for another
            category"""
        ow = MonthOverview( self.getAW(), \
                        self.getDate(), \
                        [categid] )
        ow.setDetailLevel( self.getDetailLevel() )
        return ow
