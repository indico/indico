# -*- coding: utf-8 -*-
##
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
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

from datetime import datetime,date
import calendar
import time
import random
import MaKaC.webinterface.pages.main as main
from MaKaC.i18n import _
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.wcomponents as wcomponents
from MaKaC.webinterface.pages.main import WPMainBase
from MaKaC.webinterface.pages.base import WPNotDecorated
from MaKaC.common.Configuration import Config
from MaKaC import conference
from copy import copy
from MaKaC.common.Counter import Counter
from MaKaC.common.utils import HolidaysHolder
import MaKaC.common.timezoneUtils as timezoneUtils


class WPCalendarBase( WPMainBase ):

    def __init__( self, rh, calendar, categ=None ):
        main.WPMainBase.__init__( self, rh )
        self._cal  = calendar
        self._categ = categ
        self._locTZ = timezoneUtils.DisplayTZ(self._getAW(),None,useServerTZ=1).getDisplayTZ()

    def _getTitle(self):
        return WPMainBase._getTitle(self) + " - " + _("Calendar Overview")

class WPSimpleCalendarBase( WPNotDecorated ):

    def __init__( self, rh, month, year, day, form ):
        # month/year indicates which month should be displayed in the calendar
        # day indicates if a day should be highlighted in the calendar
        WPNotDecorated.__init__( self, rh )
        self._month  = month
        self._year = year
        self._day = day
        self._form = form


class CategColorList:
    _colorList = ["#f4dabe",  "#bcdff2", "#f7f4c0", "#CCFF99", "#e0baef", "#ecf409", "#FFFFCC" ]

    def __init__( self, categList ):
        self._colorDict = {}
        self._colorIdx = 0
        for categ in categList:
            self._colorDict[categ.getId()] = self.getNewColor()

    def getNewColor( self ):
        if self._colorIdx >= len( self._colorList ):
            r = random.randint(130,255)
            g = random.randint(130,255)
            b = random.randint(130,255)
            return "#%X%X%X"%(r,g,b)
            #return "#CCCCCC"
        else:
            color = self._colorList[self._colorIdx]
            self._colorIdx += 1
            return color

    def getColor( self, categ ):
        if not self._colorDict.has_key( categ.getId() ):
            return None
        return self._colorDict[ categ.getId() ]


class WCalendarMonthItem:

    def __init__( self, month, multipleColor, categColors, cal ):
        self._month = month
        self._cal = cal
        self._multipleColor = multipleColor
        self._categColors = categColors

    def _getDiv( self, day ):
        fulldate = "%s%02d%02d" % (self._month.getYear(),self._month.getMonthNumber(),day.getDayNumber())
        res = [ """
<div id="d%s" class="calendarList">
  <table cellSpacing=0 cellPadding=1 bgcolor="#A0A0A0" border=0>
    <tr>
      <td valign=top>
        <table cellSpacing=0 cellPadding=4 bgcolor="#FFFFFF" border=0>"""%fulldate ]
        for conf in day.getConferences():
            categs = self._cal.getConferenceCategories( conf )
            if len(categs) > 1:
                colors = ["""
                <table cellspacing="0" cellpadding="0" border="0" align="left">
                <tr>"""]
                for categ in categs:
                    colors.append("""<td bgcolor="%s">&nbsp;</td>"""%self._categColors.getColor( categ ))
                colors.append("""
                </tr>
                </table>""")
                maincolor = self._multipleColor
            else:
                colors = []
                maincolor = self._categColors.getColor( categs[0] )
            title = conf.getTitle()
            res.append("""
          <tr bgcolor="#ECECEC" %s>
            <td valign=top>%s<a href="%s?confId=%s">%s</a></td>
          </tr>""" % (maincolor,"\n".join(colors),urlHandlers.UHConferenceDisplay.getURL(), conf.getId(),title))
        res.append("""
        </table>
      </td>
    </tr>
  </table>
</div>""")
        res.append("""
<script type="text/javascript">
<!--
  menudivs["d%s"]              = new Object();
  menudivs["d%s"].id           = "d%s";
  menudivs["d%s"].anchorId     = "a%s";
  menudivs["d%s"].spanId       = "s%s";
  menudivs["d%s"].menuOn       = false;
  menudivs["d%s"].onAnchor     = false;
//-->
</script>
"""%(fulldate,fulldate,fulldate,fulldate,fulldate,fulldate,fulldate,fulldate,fulldate))
        return "\n".join(res)


    def getHTML( self ):
        res = []
        divs = []

        for day in self._month.getDayList():
            fulldate = "%s%02d%02d" % (self._month.getYear(),self._month.getMonthNumber(),day.getDayNumber())
            if day.getDayNumber() == 1:
                for i in range(day.getWeekDay()):
                    res.append("<td></td>")
            categs = day.getCategories()
            if len(categs)>1:
                colors = ["""
                <table cellspacing="0" cellpadding="0" border="0" align="left">
                <tr>"""]
                for categ in categs:
                    colors.append("""<td bgcolor="%s">&nbsp;</td>"""%self._categColors.getColor( categ ))
                colors.append("""
                </tr>
                </table>""")
                res.append( """<td align="right" bgcolor="%s"  onMouseOver="setOnAnchor('d%s')" onMouseOut="clearOnAnchor('d%s')">%s<span style="cursor: default;" id="a%s">%s</span></td>"""%( self._multipleColor, fulldate, fulldate, "\n".join(colors), fulldate, day.getDayNumber() ) )
                divs.append(self._getDiv(day))
            elif len(categs) == 1:
                res.append( """<td align="right" bgcolor="%s" onMouseOver="setOnAnchor('d%s')" onMouseOut="clearOnAnchor('d%s')"><span style="cursor: default;" id="a%s">%s</span></td>"""%( self._categColors.getColor( categs[0] ), fulldate, fulldate, fulldate, day.getDayNumber() ) )
                divs.append(self._getDiv(day))
            else:
                res.append( """<td align="right">%s</td>"""%day.getDayNumber() )
            if day.getWeekDay() == 6:
                res.append("""
                    </tr>
                    <tr>\n""")
        str = _("""
                <table cellspacing="1" cellpadding="5">
                    <tr>
                        <td colspan="7" align="center" style="font-size: 1.2em;">%s %s</b></td>
                    </tr>
                    <tr>
                        <td align="right" bgcolor="#CCCCCC"> _("Mo")</td>
                        <td align="right" bgcolor="#CCCCCC">_("Tu")</td>
                        <td align="right" bgcolor="#CCCCCC">_("We")</td>
                        <td align="right" bgcolor="#CCCCCC">_("Th")</td>
                        <td align="right" bgcolor="#CCCCCC">_("Fr")</td>
                        <td align="right" bgcolor="#CCCCCC">_("Sa")</td>
                        <td align="right" bgcolor="#CCCCCC">_("Su")</td>
                    </tr>
                    <tr>
                        %s
                    </tr>
                </table>
                %s
              """)%(self._month.getName(), self._month.getYear(), "\n".join(res),"\n".join(divs))
        return str

class WCalendar(wcomponents.WTemplated):
    _multipleColor = "#DDDDDD"

    def __init__( self, aw, cal):
        self._aw = aw
        self._cal = cal

    def _getLegendItem( self, color, caption ):
        str = """<div style="font-size: 15px; margin-bottom: 5px;">
                    <div style="border: 1px solid #AAAAAA; float: left; width: 15px; height: 15px; background-color: %s"></div>
                    <span style="padding-left: 10px">%s</span>
                 </div>
              """%( color, caption )
        return str

    def _getLegend( self, categDisplayURLGen ):
        cl = CategColorList( self._cal.getCategoryList() )
        l = []
        for categ in self._cal.getCategoryList():
            url = categDisplayURLGen( categ )
            caption = """<a href="%s">%s</a>"""%( url, categ.getName() )
            l.append( """%s"""%self._getLegendItem(cl.getColor(categ), caption) )
        l.append( """%s"""%self._getLegendItem( self._multipleColor, _("Multiple") ) )

        return """%s """%("".join(l))

    def _getCalendar( self ):
        cl = CategColorList( self._cal.getCategoryList() )
        res = ["<tr>"]
        idx = 0
        for month in self._cal.getMonthList():
            if idx == self._cal.getNrColumns():
                res.append("</tr>\n<tr>")
                idx = 0
            m = WCalendarMonthItem( month, self._multipleColor, cl, self._cal)
            res.append(""" <td valign="top">%s</td>"""%m.getHTML() )
            idx += 1
        res.append("</tr>")
        return "".join( res )

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        locNM = self._cal.getLocator()
        del locNM["months"]
        vars["locatorNoMonth"]= locNM.getWebForm()
        vars["locator"]= self._cal.getLocator().getWebForm()
        for i in range(6, 13):
            if self._cal.getNrMonths() == i:
                vars["def%s"%i] = "selected"
            else:
                vars["def%s"%i] = ""
        vars["legend"] = self._getLegend( urlHandlers.UHCategoryDisplay.getURL )
        vars["calendar"] = self._getCalendar()
        vars["selectedmonths"] = int(self._cal.getNrMonths())
        vars["selectedcolumns"] = int(self._cal.getNrColumns())
        vars["selectedmonth"] = int(self._cal.getStartDate().strftime("%m"))
        vars["selectedyear"] = int(self._cal.getStartDate().strftime("%Y"))
        return vars


class WPCalendar( WPCalendarBase ):

    def _getBody( self, params ):
        wc = WCalendar( self._getAW(), self._cal )
        cat = self._categ
        catman=conference.CategoryManager()
        catList=[]
        for cat in self._cal.getCategoryList():
            while cat.getId()!="0":
                cat = cat.getOwner()
                catList.append(cat.getId())
        params = { "changeMonthsURL": urlHandlers.UHCalendar.getURL(), \
                   "categDisplayURL": urlHandlers.UHCategoryDisplay.getURL(self._categ), \
                   "selCategsURL": str(urlHandlers.UHCalendarSelectCategories.getURL()), \
                   "categoryTitle": self._categ.getTitle() \
                 }
        params["selCategsURL"] += "?xs="+catman.getRoot().getId()
        for id in catList:
            params["selCategsURL"] += "&xs="+id
        return wc.getHTML( params )

    def _getNavigationDrawer(self):
        link = [{"url": urlHandlers.UHCalendar.getURL([self._categ]), "title": _("Calendar overview"), "type": "Calendar"}]
        pars = {"target": self._categ, "isModif": False}
        return wcomponents.WNavigationDrawer( pars, appendPath = link )


class MulSelectCategTree:

    def __init__( self, aw ):
        self._aw = aw
        self._number = Counter()
    def _getItem( self, categ, level=0 ):
        if not categ.canView( self._aw ):
            return ""
        html = ""
        number=self._number.newCount()
        for i in range(level):
            html = "%s&nbsp;&nbsp;&nbsp;"%html
        cfg = Config.getInstance()
        checked = ""

        if categ in self._selCategs:
            checked = "checked"
        title = """<input type="checkbox" name="selCateg" id="%s" onClick="alerta(%s);" value="%s" %s> %s"""%\
                    (number,number,categ.getId(), checked, categ.getName() )
        if categ in self._expandedCategs:
            temp = copy( self._expandedCategs )
            temp.remove( categ )
            html = """%s<a href="%s"><img src="%s" border="0" alt="fold"></a> %s"""%\
                (   html, \
                    self._expandURLGen( temp ), \
                    cfg.getSystemIconURL("itemExploded"), \
                    title )
            for subcat in categ.getSubCategoryList():
                html = "%s<br>%s"%(html, self._getItem(subcat, level+1) )
        else:
            html = """%s<a href="%s"><img src="%s" border="0" alt="unfold"></a> %s"""%\
                (   html, \
                    self._expandURLGen( self._expandedCategs+[categ] ), \
                    cfg.getSystemIconURL("itemCollapsed"), \
                    title )
        return html


    def getHTML( self, selected, expanded, expandURLGen ):
        self._selCategs = selected
        self._expandedCategs = expanded
        self._expandURLGen = expandURLGen
        r = conference.CategoryManager().getRoot()
        return self._getItem( r )


class WCalendarSelectCategs( wcomponents.WTemplated ):

    def __init__( self, aw, cal ):
        self._aw = aw
        self._cal = cal

    def getHTML( self, expanded, expandURLGen, calendarURL ):
        self._exp = expanded
        self._expURLGen = expandURLGen
        self._calURL = calendarURL
        return wcomponents.WTemplated.getHTML( self, {} )

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        l = self._cal.getLocator()
        vars["locator"] = l.getWebForm()
        del l["selCateg"]
        vars["locatorNoCategs"] = l.getWebForm()
        vars["categs"] = MulSelectCategTree( self._aw ).getHTML( \
                                        self._cal.getCategoryList(), \
                                        self._exp, self._expURLGen )
        vars["calendarURL"] = self._calURL
        return vars


class WPCalendarSelectCategories( WPCalendarBase ):

    def _getExpandedCategURL( self, exList ):
        url = urlHandlers.UHCalendarSelectCategories.getURL( self._cal )
        ex = []
        for categ in exList:
            ex.append( categ.getId() )
        url.addParam( "xs", ex )
        return url

    def _getBody( self, params ):
        wc = WCalendarSelectCategs( self._getAW(), self._cal )
        return wc.getHTML( params["expanded"], \
                            self._getExpandedCategURL, \
                            urlHandlers.UHCalendar.getURL() )


class WSimpleCalendar(wcomponents.WTemplated):

    def __init__( self, aw, month, year, date ):
        # month/year indicates which month should be displayed in the calendar
        # date indicates if a day should be highlighted in the calendar
        self._aw = aw
        self._month = int(month)
        self._year = int(year)
        self._date = date

    def _displayMonth( self ):
        month = self._month
        year = self._year
        today = date.today()
        res = []
        for day in range(1,calendar.monthrange(year,month)[1]+1):
            if day == 1:
                for i in range(calendar.weekday(year,month,day)):
                    res.append("<td></td>")
            #calendar.weekday(year,month,day) in (5,6):
            if HolidaysHolder.isWorkingDay( datetime( year, month, day ) ):
                bgcolor="#FFFFFF"
            else:
                bgcolor="#EEEEEE"
            if date(year,month,day) == today:
                bgcolor="#ccffcc"
            if self._date != '':
                (d,m,y) = self._date.split("-")
                if date(year,month,day) == date(int(y),int(m),int(d)):
                    bgcolor="#ffcccc"
            res.append( """<td align="right" bgcolor="%s"><a href="" onClick="SetDate(%s,%s,%s);">%s</a></td>"""%(bgcolor,day,month,year,day ))
            if calendar.weekday(year,month,day) == 6:
                res.append("</tr><tr>")
        str = _("""
                <table>
                    <tr>
                        <td colspan="7" align="center"><b>
                        <a href="javascript:PreviousYear();">&lt;&lt;</a>
                        &nbsp;
                        <a href="javascript:PreviousMonth();">&lt;</a>
                        %s %s
                        <a href="javascript:NextMonth();">&gt;</a>
                        &nbsp;
                        <a href="javascript:NextYear();">&gt;&gt;</a>
                        </b></td>
                    </tr>
                    <tr>
                        <td align="right" bgcolor="#CCCCCC">_("Mo")</td>
                        <td align="right" bgcolor="#CCCCCC">_("Tu")</td>
                        <td align="right" bgcolor="#CCCCCC">_("We")</td>
                        <td align="right" bgcolor="#CCCCCC">_("Th")</td>
                        <td align="right" bgcolor="#CCCCCC">_("Fr")</td>
                        <td align="right" bgcolor="#CCCCCC">_("Sa")</td>
                        <td align="right" bgcolor="#CCCCCC">_("Su")</td>
                    </tr>
                    <tr>
                        %s
                    </tr>
                </table>
              """) %(datetime(1900,month,1).strftime("%B"), year, "\n".join(res))
        return str

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["calendar"] = self._displayMonth()
        vars["date"] = self._date
        return vars


class WPSimpleCalendar( WPSimpleCalendarBase):

    def _getBody( self, params ):
        wc = WSimpleCalendar( self._getAW(), self._month, self._year, self._day )
        pars = { "daystring": self._rh.getRequestParams().get('daystring',""),
                "monthstring": self._rh.getRequestParams().get('monthstring', ""),
                "yearstring": self._rh.getRequestParams().get('yearstring', ""),
                "month": self._rh.getRequestParams().get('month', str(datetime.now().strftime("%m"))),
                "year": self._rh.getRequestParams().get('year', str(datetime.now().strftime("%Y"))),
                "form": self._rh._form }
        return wc.getHTML( pars )

class SimpleOverviewCalendar(wcomponents.WTemplated):

    def __init__( self, aw, month, year, date,type,id):
        # month/year indicates which month should be displayed in the calendar
        # date indicates if a day should be highlighted in the calendar
        self._aw = aw
        self._month = int(month)
        self._year = int(year)
        self._date = date
        self._type = type
        self._id = id

    def _displayMonth( self):
        id=self._id
        type=self._type
        month = self._month
        year = self._year
        today = date.today()
        res = []


        url = urlHandlers.UHGetCalendarOverview.getURL()
        url.addParam("selCateg", id)
        url.addParam("period",type)

        nextMonth= urlHandlers.UHGetCalendarOverview.getURL()
        previousMonth= urlHandlers.UHGetCalendarOverview.getURL()
        nextYear= urlHandlers.UHGetCalendarOverview.getURL()
        previousYear= urlHandlers.UHGetCalendarOverview.getURL()

        nextMonth.addParam("selCateg", id)
        previousMonth.addParam("selCateg", id)
        nextYear.addParam("selCateg", id)
        previousYear.addParam("selCateg", id)

        nextMonth.addParam("period",type)
        previousMonth.addParam("period",type)
        nextYear.addParam("period",type)
        previousYear.addParam("period",type)


        for day in range(1,calendar.monthrange(year,month)[1]+1):
            if day == 1:
                for i in range(calendar.weekday(year,month,day)):
                    res.append("<td></td>")
            if calendar.weekday(year,month,day) in (5,6):
                bgcolor="#e0cdcd"
            else:
                bgcolor="#FFFFFF"
            if self._date != []:
                #for highlight multiple dates
                for date2 in self._date:
                    (d,m,y) = date2.split("-")

                    try:
                        if date(year,month,day) == date(int(y),int(m),int(d)):
                            bgcolor="#ffcccc"
                    except Exception,e:
                        raise "%s-%s-%s------%s-%s-%s\nself._date:%s\ndate2:%s"%(year,month,day,y,m,d, self._date,date2)

                    url.addParam("day", day)
                    url.addParam("month",month)
                    url.addParam("year", year)
                    strUrl = "%s"%url

            if date(year,month,day) == today:
                bgcolor="#ccffcc"

            res.append( """<td align="right" bgcolor="%s"><a href="%s">%s</a></td>"""%(bgcolor,strUrl,day ))

            if calendar.weekday(year,month,day) == 6:
                res.append("</tr><tr>")

        if month >=12:
            nextMonth.addParam("year",year+1)
            nmonth = 1
        else:
            #if next month does not have 'd' day, move to next next month
            nextMonth.addParam("year", year)
            nmonth = month + 1

        nextMonth.addParam("month", nmonth)
        mrange = calendar.monthrange(year, nmonth)[1]
        if int(d) > mrange:
            nextMonth.addParam("day", mrange)
        else:
            nextMonth.addParam("day", d)

        if month <= 1:
            pmonth = 12
            previousMonth.addParam("year", year-1)
        else:
            pmonth = month - 1
            previousMonth.addParam("year", year)

        previousMonth.addParam("month",pmonth)
        mrange = calendar.monthrange(year, pmonth)[1]
        if int(d) > mrange:
            previousMonth.addParam("day", mrange)
        else:
            previousMonth.addParam("day", d)

        nextYear.addParam("day",d)
        nextYear.addParam("month",month)
        nextYear.addParam("year",year+1)
        previousYear.addParam("day",d)
        previousYear.addParam("month",month)
        previousYear.addParam("year",year-1)

        strnm = "%s"%nextMonth
        strpm = "%s"%previousMonth
        strny = "%s"%nextYear
        strpy = "%s"%previousYear
        html = _("""
                <table cellspacing="1" cellpadding="5">
                    <tr>
                        <td colspan="7" align="center" style="font-size: 1.1em;">
                        <a href="%s">&lt;&lt;</a>
                        &nbsp;
                        <a href="%s">&lt;</a>
                        &nbsp;
                        %s %s
                        &nbsp;
                        <a href="%s">&gt;</a>
                        &nbsp;
                        <a href="%s">&gt;&gt;</a>
                        </td>
                    </tr>
                    <tr>
                        <td align="right" bgcolor="#CCCCCC">_("Mo")</td>
                        <td align="right" bgcolor="#CCCCCC">_("Tu")</td>
                        <td align="right" bgcolor="#CCCCCC">_("We")</td>
                        <td align="right" bgcolor="#CCCCCC">_("Th")</td>
                        <td align="right" bgcolor="#CCCCCC">_("Fr")</td>
                        <td align="right" bgcolor="#CCCCCC">_("Sa")</td>
                        <td align="right" bgcolor="#CCCCCC">_("Su")</td>
                    </tr>
                    <tr>
                        %s
                    </tr>
                </table>
              """) %(strpy,strpm,datetime(1900,month,1).strftime("%B"), year,strnm,strny, "\n".join(res))
        return html


    #def getVars( self ):
    #    vars = wcomponents.WTemplated.getVars( self )
    #    vars["calendar"] = self._displayMonth()
    #    vars["date"] = self._date
    #    return vars
