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

import sys,re
import datetime,sets

from MaKaC.common.general import *
from MaKaC.common import db
from MaKaC.conference import ConferenceHolder,CategoryManager
from MaKaC.common import indexes
from MaKaC.webinterface.urlHandlers import UHMaterialDisplay, UHConferenceDisplay
from MaKaC.common.timezoneUtils import nowutc
import MaKaC.common.info as info
from pytz import timezone

#######################################################
#
# Name:          SSLPdisplay.py
# Description:   Create the SSLP program page
# Author:        T.Baron
#
# Last modified:  10/03/2003 - adapted to cdsdoc
#
# Input: 1/Year yyyy
#
#######################################################

def usage():
    return "usage: SSLPdisplay.py?stdate=yyyy-mm-dd&nbweeks=xxx";

def sortByStartDate(conf1,conf2):
  ch = ConferenceHolder()
  return cmp(ch.getById(conf1).getStartDate().time(),ch.getById(conf2).getStartDate().time())

def index(req, **params):
    """This script displays the list of meetings which are planned in the
    coming week"""
    global ids
    try:
      stdate = params['stdate']
      nbweeks = params['nbweeks']
    except:
      return usage()
    [year,month,day] = stdate.split("-")
    days = int(nbweeks) * 7
    ch = ConferenceHolder()
    previous = ""
    if str(year) == "2008":
        previous = """<a href="http://indico.cern.ch/tools/SSLPdisplay.py?stdate=2007-07-02&nbweeks=7">Previous Year Lecture Programme</a>"""
    elif str(year) == "2009":
        previous = """<a href="http://indico.cern.ch/tools/SSLPdisplay.py?stdate=2008-06-30&nbweeks=9">Previous Year Lecture Programme</a>"""
    elif str(year) == "2010":
        previous = """<a href="http://indico.cern.ch/tools/SSLPdisplay.py?stdate=2009-06-29&nbweeks=8">Previous Year Lecture Programme</a>"""

    html = """
<!doctype html public "-//w3c//dtd html 4.0 transitional//en">
<html>
<head>
   <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1">
   <meta name="Author" content="Matthias Egger">
   <meta name="GENERATOR" content="Mozilla/4.75 [en] (Win95; U) [Netscape]">
   <meta name="resp1" content="Matthias Egger">
   <meta name="resp2" content="Tanja Peeters">
   <meta name="DateCreated" content="971205">
   <meta name="DateExpires" content="981201">
   <meta name="DateModified" content="971205">
   <meta name="Keywords" content="summer student lecture programme">
   <meta name="Description" content="The Summer Student lecture programme.">
   <title>Summer Student Lecture Programme</title>
</head>
<body text="#000099" bgcolor="#FFFFCC" link="#000000" vlink="#C6600" alink="#FF9900">

<div align=right></div>
<map name="cern_options_banner_2"><area shape="rect" coords="1,16,70,35" href="http://cern.web.cern.ch/CERN/Divisions/PE/HRS/Recruitment/Welcome.html"><area shape="rect" coords="72,17,146,35" href="http://cern.web.cern.ch/CERN/Divisions/PE/HRS/Recruitment/youngpeople.html"><area shape="rect" coords="146,15,181,37" href="http://cern.web.cern.ch/CERN/Divisions/PE/HRS/Recruitment/staff.html"><area shape="rect" coords="182,15,224,38" href="http://cern.web.cern.ch/CERN/Divisions/PE/HRS/Recruitment/fellows.html"><area shape="rect" coords="225,15,286,38" href="http://cern.web.cern.ch/CERN/Divisions/PE/HRS/Recruitment/associates.html"><area shape="rect" coords="286,16,337,37" href="http://cern.web.cern.ch/CERN/Divisions/PE/HRS/Recruitment/students.html"><area shape="rect" coords="338,16,389,36" href="http://cern.web.cern.ch/CERN/Divisions/PE/HRS/Recruitment/aboutus.html"><area shape="rect" coords="391,17,449,35" href="http://cern.web.cern.ch/CERN/Divisions/PE/HRS/Recruitment/contactus.html"><area shape="rect" coords="450,16,503,35" href="http://cern.web.cern.ch/CERN/Divisions/PE/HRS/Recruitment/other.html"><area shape="rect" coords="506,2,552,46" href="http://www.cern.ch"><area shape="default" nohref></map>
%s
<br>
<br>
<center>
<p><a NAME="Prog"></a><b><font face="Verdana"><font color="#000080"><font size=+2>Summer Student Lecture Programme %s </font></font></font></b></center>
</font></font></font>
<p><b><font face="Verdana"><font color="#000080"><font size=-1>Keys:</font></font></font></b>
<br><font face="Verdana"><font size=-1><font color="green">(v): videos</font></font></font>
<br><font face="Verdana"><font size=-1><font color="red">(t): transparencies</font></font></font>
<br><font face="Verdana"><font size=-1><font color="brown">(l): web lecture</font></font></font>
<br><font face="Verdana"><font size=-1><font color="blue">(b): biography</font></font></font>
<br><font face="Verdana"><font size=-1><font color="grey">(q): questionnaire</font></font></font>
<br>&nbsp;""" % (previous,year)

    #create list of ids
    ids = [345,346,347,348]
    db.DBMgr.getInstance().startRequest()
    tz = info.HelperMaKaCInfo.getMaKaCInfoInstance().getTimezone()
    #create date object
    startdate = timezone(tz).localize(datetime.datetime(int(year),int(month),int(day)))
    stdatedays = startdate.toordinal()
    enddate   = startdate + datetime.timedelta(days=int(days))
    #create result set
    res = sets.Set()

    #instanciate indexes
    im = indexes.IndexesHolder()
    catIdx = im.getIndex('category')
    calIdx = im.getIndex('calendar')

    c1 = calIdx.getObjectsIn(startdate, enddate)
    for id in ids:
      confIds=sets.Set(catIdx.getItems(id))
      confIds.intersection_update(c1)
      res.union_update(confIds)

    res = list(res)
    res.sort(sortByStartDate)

    seminars = {}
    stimes = []
    etimes = []

    for id in res:
        obj = ch.getById(id)
        agenda={}
        agenda['object'] = obj
        agenda['id'] = obj.getId()
        agenda['stime1'] = obj.getAdjustedStartDate(tz).time().isoformat()[0:5]
        agenda['atitle'] = obj.getTitle()
        agenda['desc'] = ""
        if obj.getComments() != "":
            agenda['desc'] = "<br>%s" % obj.getComments()
        if obj.getChairList() != []:
            agenda['chairman'] = obj.getChairList()[0].getFullName()
        else:
            agenda['chairman'] = ""
        agenda['stdate'] = obj.getAdjustedStartDate(tz).date()
        agenda['fduration'] = (obj.getAdjustedEndDate(tz)-obj.getAdjustedStartDate(tz)).seconds
        agenda['etime1'] = obj.getAdjustedEndDate(tz).time().isoformat()[0:5]
        stime = obj.getAdjustedStartDate(tz).time().isoformat()[0:5]
        etime = obj.getAdjustedEndDate(tz).time().isoformat()[0:5]
        stdate = obj.getAdjustedStartDate(tz).date()
        if not seminars.has_key(stdate):
            seminars[stdate] = {}
        if not seminars[stdate].has_key(stime):
            seminars[stdate][stime] = []
        seminars[stdate][stime].append(agenda)
        if not stime in stimes:
            stimes.append(stime)
            etimes.append(etime)

    for week in range(0,int(nbweeks)):
        html += """<table BORDER CELLPADDING=4 WIDTH="100%" >
<tr>
<td VALIGN=TOP WIDTH="6%" HEIGHT="27" BGCOLOR="#FFFFFF">
<center><b><font face="Arial">Time</font></b></center>
</td>"""
        beginweek = stdatedays+(week*7)
        endweek = stdatedays+(week+1)*7-2

        # display day names
        days = beginweek
        while days < endweek:
            thisday = datetime.datetime.fromordinal(days).strftime("%A %d %b")
            html += """
<td VALIGN=TOP WIDTH="19%%" HEIGHT="27" BGCOLOR="#FFFFFF">
<center><b><font face="Arial">%s</font></b></center>
</td>""" % thisday
            days+=1

        html+= "</TR>"

        #display hour per hour agenda
        rowtext = ""
        for i in range(len(stimes)):
            val = stimes[i]
            rowtext = ""
            nbtalks = 0
            rowtext += """
<TR><td VALIGN=TOP WIDTH="6%%" BGCOLOR="#FFFFFF">
<center><b><font face="Arial">%s</font></b>
<br><b><font face="Arial">-</font></b>
<br><b><font face="Arial">%s</font></b></center>
</td>""" % (stimes[i],etimes[i])

            days = beginweek
            while days < endweek:
                thisday = datetime.date.fromordinal(days)
                texttime = ""
                if seminars.has_key(thisday) and seminars[thisday].has_key(val):
                    for agenda in seminars[thisday][val]:
                        ida = agenda['id']
                        if agenda['stime1'] != stimes[i] or agenda['etime1'] != etimes[i]:
                            texttime = "<BR><i>("+agenda['stime1']+" - "+agenda['etime1']+")</i>"
                        #FILES
                        textfiles = "";
                        miscitems = 0;
                        for m in agenda['object'].getAllMaterialList():
                            entry = m.getTitle().lower()
                            if entry[0:4] != "part":
                                if entry == "video" or entry == "video in cds":
                                    entry = "<font color=green>v</font>"
                                elif entry in ["transparencies","slides"]:
                                    entry = "<font color=red>t</font>"
                                elif entry in ["biography"]:
                                    entry = "<font color=blue>b</font>"
                                elif entry == "questionnaire":
                                    entry = "<font color=grey>q</font>"
                                elif entry == "syncomat":
                                    entry = "<font color=brown>l</font>"
                                elif entry == "lecture":
                                    entry = "<font color=brown>l</font>"
                                elif entry == "lecture_from_2000":
                                    entry = "<font color=brown>l/2000</font>"
                                elif entry == "video_from_2000":
                                    entry = "<font color=green>v/2000</font>"
                                else:
                                    entry = "m"
                                url = UHMaterialDisplay.getURL(m)
                                textfiles += "(<A HREF=%s>%s</A>)" % (url,entry)

                        rowtext += """<td VALIGN=TOP WIDTH="19%%"><font face="Arial"><font size=-1><a href="%s">%s</a>%s%s</font></font><p><i><font face="Arial"><font size=-1><i>%s</I>%s</font></font></i></td>\n""" % ( UHConferenceDisplay.getURL(agenda['object']),agenda['atitle'],agenda['desc'],textfiles,agenda['chairman'],texttime )
                        nbtalks+=1
                else:
                    rowtext += """<td VALIGN=TOP WIDTH="19%">&nbsp;</td>"""
                days+=1
            rowtext += "</TR>"
            if nbtalks != 0:
                html+=rowtext

    html+="</TABLE>"
    html+="<br>&nbsp;"

    html += """
<br>&nbsp;
<!--
<p><a href="http://cern.web.cern.ch/CERN/Divisions/PE/HRS/Recruitment/6sumprog.html#SUMMER STUDENTS">CERN Recruitment Service</a>
-->
<center>
<hr WIDTH="100%">
<!--
<br><font face="Verdana,Helvetica,Helvetica"><font size=-2><font color="#A00000"><a href="http://cern.web.cern.ch/CERN/Divisions/PE/HRS/Recruitment/search_HRS.html">Search</a></font><font color="#0000A0">
the pages of the Recruitment Service</font></font></font>
<br><font face="Verdana,Helvetica"><font color="#000099"><font size=-2>
Comments about this Web site to: <a href="mailto:WWW.Recruitment@cern.ch">WWW.Recruitment@cern.ch</a></font></font></font>
<br><font face="Verdana,Helvetica"><font color="#000099"><font size=-2>Enquiries
about Recruitment Programmes to: <a href="mailto:Recruitment.Service@cern.ch">Recruitment.Service@cern.ch</a></font></font></font>
-->
<br><font face="Verdana,Helvetica"><font color="#000099"><font size=-2>Copyright
CERN - the European Laboratory for Particle Physics (Geneva, Switzerland)</font></font></font></center>

<p><br>
</body>
</html>"""

    return html
