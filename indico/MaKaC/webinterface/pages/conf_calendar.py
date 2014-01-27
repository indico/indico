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

from datetime import datetime, date
import calendar
import time
import random
import MaKaC.webinterface.pages.main as main
from MaKaC.i18n import _
from indico.util.i18n import i18nformat, currentLocale
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.wcomponents as wcomponents
from MaKaC.webinterface.pages.main import WPMainBase
from MaKaC.webinterface.pages.base import WPNotDecorated
from indico.core.config import Config
from MaKaC import conference
from copy import copy
from MaKaC.common.Counter import Counter
from MaKaC.common.utils import HolidaysHolder
import MaKaC.common.timezoneUtils as timezoneUtils
from MaKaC.errors import MaKaCError


class WPCalendarBase( WPMainBase ):

    def __init__( self, rh, calendar, categ=None ):
        main.WPMainBase.__init__( self, rh )
        self._cal  = calendar
        self._categ = categ
        self._locTZ = timezoneUtils.DisplayTZ(self._getAW(),None,useServerTZ=1).getDisplayTZ()

    def _getTitle(self):
        return WPMainBase._getTitle(self) + " - " + _("Calendar Overview")


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
            <td valign=top>%s<a href="%s">%s</a></td>
          </tr>""" % (maincolor, "\n".join(colors), urlHandlers.UHConferenceDisplay.getURL(conf), title))
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
        str = i18nformat("""
                <table cellspacing="1" cellpadding="5">
                    <tr>
                        <td colspan="7" align="center" style="font-size: 1.2em;">%s %s</b></td>
                    </tr>
                    <tr>
                      %s
                    </tr>
                    <tr>
                        %s
                    </tr>
                </table>
                %s
                """) % (self._month.getName(), self._month.getYear(),
                        ''.join(list('<td align="right" bgcolor="#CCCCCC">%s</td>' % currentLocale().weekday(wd)[:2] for wd in xrange(0, 7))),
                        "\n".join(res),"\n".join(divs))

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


class WPCalendar(WPCalendarBase):

    def _getBody(self, params):
        wc = WCalendar(self._getAW(), self._cal)
        cat = self._categ
        catman = conference.CategoryManager()
        catList = []
        for cat in self._cal.getCategoryList():
            while cat.getId() != "0":
                cat = cat.getOwner()
                catList.append(cat.getId())
        params = {"changeMonthsURL": urlHandlers.UHCalendar.getURL(),
                  "categDisplayURL": urlHandlers.UHCategoryDisplay.getURL(self._categ),
                  "selCategsURL": str(urlHandlers.UHCalendarSelectCategories.getURL()),
                  "categoryTitle": self._categ.getTitle(),
                  "currentYear": datetime.now().year,
                  }
        params["selCategsURL"] += "?xs=" + catman.getRoot().getId()
        for id in catList:
            params["selCategsURL"] += "&xs=" + id
        return wc.getHTML(params)

    def _getNavigationDrawer(self):
        #link = [{"url": urlHandlers.UHCalendar.getURL([self._categ]), "title": _("Calendar overview")}]
        pars = {"target": self._categ, "isModif": False}
        return wcomponents.WNavigationDrawer( pars, type = "Calendar" )


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
