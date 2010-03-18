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

from xml.sax.saxutils import quoteattr, escape
from datetime import datetime,timedelta

import MaKaC.webinterface.wcomponents as wcomponents
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.materialFactories as materialFactories
import MaKaC.webinterface.navigation as navigation
import MaKaC.schedule as schedule
import MaKaC.conference as conference
import MaKaC.webinterface.linking as linking
from MaKaC.webinterface.pages.conferences import WScheduleContribution, WPConferenceBase, WPConfModifScheduleGraphic, WPConferenceDefaultDisplayBase, WContribParticipantList, WContributionCreation, WContributionSchCreation, WPModScheduleNewContribBase, WPConferenceModifBase
from MaKaC.common import Config, info
from MaKaC.errors import MaKaCError
import MaKaC.webinterface.timetable as timetable
from MaKaC.webinterface.common.contribStatusWrapper import ContribStatusList
import MaKaC.common.filters as filters
import MaKaC.webinterface.common.contribFilters as contribFilters
from MaKaC.webinterface.common.person_titles import TitlesRegistry
from MaKaC.webinterface.pages import main
from MaKaC.common.utils import isStringHTML
from MaKaC import user
from MaKaC.i18n import _

from pytz import timezone
from MaKaC.common.PickleJar import DictPickler
import simplejson
import pytz
import copy
import MaKaC.webinterface.common.timezones as convertTime
import MaKaC.common.timezoneUtils as timezoneUtils


class WPSessionBase( WPConferenceBase ):

    def __init__( self, rh, session):
        self._session = session
        WPConferenceBase.__init__( self, rh, self._session.getConference() )


class WPSessionDisplayBase( WPSessionBase ):
    pass

class WPSessionDefaultDisplayBase( WPConferenceDefaultDisplayBase, WPSessionDisplayBase ):

    def __init__( self, rh, session ):
        WPSessionDisplayBase.__init__( self, rh, session )

class WContributionDisplayItemBase(wcomponents.WTemplated):

    def __init__(self,aw,contrib):
        self._contrib=contrib
        self._aw=aw

    def getVars( self ):
        vars=wcomponents.WTemplated.getVars( self )
        vars["id"]=self.htmlText(self._contrib.getId())
        vars["title"]=self.htmlText(self._contrib.getTitle())
        cType=""
        if self._contrib.getType() is not None:
            cType=self.htmlText(self._contrib.getType().getName())
        vars["type"]=self.htmlText(cType)
        vars["startDate"]="&nbsp;"
        if self._contrib.isScheduled():
            vars["startDate"]=self._contrib.getAdjustedStartDate().strftime("%Y-%b-%d %H:%M")
        vars["duration"] = "&nbsp;"
        if self._contrib.getDuration() is not None:
            if (datetime(1900,1,1)+self._contrib.getDuration()).minute>0:
                vars["duration"]="%s"%(datetime(1900,1,1)+self._contrib.getDuration()).strftime("%M'")
            if (datetime(1900,1,1)+self._contrib.getDuration()).hour>0:
                vars["duration"]="%s"%(datetime(1900,1,1)+self._contrib.getDuration()).strftime("%Hh%M'")
        lspk = []
        for speaker in self._contrib.getSpeakerList():
            lspk.append(self.htmlText(speaker.getFullName()))
        vars["speakers"] = "<br>".join( lspk )
        if vars["speakers"]=="":
            vars["speakers"]="&nbsp;"
        vars["displayURL"]=quoteattr(str(urlHandlers.UHContributionDisplay.getURL(self._contrib)))
        vars["boardNumber"]=self.htmlText(self._contrib.getBoardNumber())
        return vars


class WContributionDisplayItemFull(WContributionDisplayItemBase):
    pass


class WContributionDisplayItemMin(WContributionDisplayItemBase):
    pass


class WContributionDisplayItem:

    def __init__( self, aw, contrib ):
        self._contribution = contrib
        self._aw = aw

    def getHTML( self, params={} ):
        if self._contribution.canAccess( self._aw ):
            c = WContributionDisplayItemFull( self._aw, self._contribution )
            return c.getHTML( params )
        if self._contribution.canView( self._aw ):
            c = WContributionDisplayItemMin( self._aw, self._contribution )
            return c.getHTML( params )
        return ""


class WContributionDisplayPosterItemFull(WContributionDisplayItemBase):
    pass


class WContributionDisplayPosterItemMin(WContributionDisplayItemBase):
    pass


class WContributionDisplayPosterItem:

    def __init__( self, aw, contrib ):
        self._contribution = contrib
        self._aw = aw

    def getHTML( self, params={} ):
        if self._contribution.canAccess( self._aw ):
            c = WContributionDisplayPosterItemFull( self._aw, self._contribution )
            return c.getHTML( params )
        if self._contribution.canView( self._aw ):
            c = WContributionDisplayPosterItemMin( self._aw, self._contribution )
            return c.getHTML( params )
        return ""


class WSessionTabControl(wcomponents.WTabControl):
    _unSelTabCls="display_unselectedhtab"
    _selTabCls="display_selectedhtab"
    _noTabCls="display_neutralhtab"


class _NoWitdhdrawFF(filters.FilterField):
    _id="no_withdrawn"

    def __init__(self):
        pass

    def satisfies(self,contrib):
        return not isinstance(contrib.getCurrentStatus(),conference.ContribStatusWithdrawn)


class _NoWithdrawnFilterCriteria(filters.FilterCriteria):

    def __init__(self,conf):
        self._fields={"no_withdrawn":_NoWitdhdrawFF()}


class WSessionDisplayBase(wcomponents.WTemplated):

    def __init__(self,aw,session,activeTab="time_table",sortingCrit=None):
        self._aw=aw
        self._session=session
        self._activeTab=activeTab
        self._sortingCrit=sortingCrit
        self._tz = timezoneUtils.DisplayTZ(self._aw,self._session.getConference()).getDisplayTZ()

    def _getHTMLRow(self,title,body):
        str = """
                <tr>
                    <td nowrap class="displayField" valign="top"><b>%s:</b></td>
                    <td>%s</td>
                </tr>"""%(title,body)
        if body.strip() == "":
            return ""
        return str

    def _createTabCtrl( self ):
        self._tabCtrl=wcomponents.TabControl()
        url=urlHandlers.UHSessionDisplay.getURL(self._session)
        url.addParam("tab","contribs")
        self._tabContribs=self._tabCtrl.newTab("contribs", \
                                                _("Contribution List"),str(url))
        url.addParam("tab","time_table")
        self._tabTimeTable=self._tabCtrl.newTab("time_table", \
                                                _("Time Table"),str(url))
        if self._session.getScheduleType()=="poster":
            self._tabTimeTable.setEnabled(False)
            self._tabCtrl.getTabById("contribs").setActive()
        else:
            self._tabTimeTable.setEnabled(True)
            tab=self._tabCtrl.getTabById(self._activeTab)
            if tab is None:
                tab=self._tabCtrl.getTabById("time_table")
            tab.setActive()

    def _getURL(self,sortByField):
        url=urlHandlers.UHSessionDisplay.getURL(self._session)
        url.addParam("tab",self._activeTab)
        url.addParam("sortBy",sortByField)
        return url

    def _getContribListHTML(self):
        cl = []
        if self._sortingCrit is None:
            self._sortingCrit=contribFilters.SortingCriteria(["number"])
        fc=_NoWithdrawnFilterCriteria(self._session.getConference())
        f=filters.SimpleFilter(fc,self._sortingCrit)
        for contrib in f.apply(self._session.getContributionList()):
            wc=WContributionDisplayItem(self._aw,contrib)
            html=wc.getHTML()
            cl.append("""<tr><td valign="top">%s</td></tr>"""%html)
        idHTML="""id <img src=%s border="0" alt="down">"""%quoteattr(str(Config.getInstance().getSystemIconURL("downArrow")))
        if self._sortingCrit.getField().getId()!="number":
            idHTML="""<a href=%s>id</a>"""%quoteattr(str(self._getURL("number")))
        dateHTML="""date <img src=%s border="0" alt="down">"""%quoteattr(str(Config.getInstance().getSystemIconURL("downArrow")))
        if self._sortingCrit.getField().getId()!="date":
            dateHTML="""<a href=%s>date</a>"""%quoteattr(str(self._getURL("date")))
        typeHTML="""type <img src=%s border="0" alt="down">"""%quoteattr(str(Config.getInstance().getSystemIconURL("downArrow")))
        if self._sortingCrit.getField().getId()!="type":
            typeHTML="""<a href=%s>type</a>"""%quoteattr(str(self._getURL("type")))
        spkHTML="""presenters <img src=%s border="0" alt="down">"""%quoteattr(str(Config.getInstance().getSystemIconURL("downArrow")))
        if self._sortingCrit.getField().getId()!="speaker":
            spkHTML="""<a href=%s>presenters</a>"""%quoteattr(str(self._getURL("speaker")))
        return """
            <table cellspacing="0" cellpadding="5" width="100%%">
                <tr>
                    <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #5294CC; padding-right:10px;border-right:5px solid #FFFFFF">%s</td>
                    <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #5294CC; padding-right:10px;border-right:5px solid #FFFFFF">%s</td>
                    <td class="titleCellFormat" style="border-bottom: 1px solid #5294CC; padding-right:10px;border-right:5px solid #FFFFFF">dur.</td>
                    <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #5294CC; padding-right:10px;border-right:5px solid #FFFFFF">%s</td>
                    <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #5294CC; padding-right:10px;border-right:5px solid #FFFFFF">title</td>
                    <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #5294CC; padding-right:10px;border-right:5px solid #FFFFFF">%s</td>
                </tr>
                %s
            </table>"""%(idHTML,dateHTML,typeHTML,spkHTML,"".join(cl))

    def _getPosterContribListHTML(self):
        cl = []
        if self._sortingCrit is None:
            self._sortingCrit=contribFilters.SortingCriteria(["number"])
        fc=_NoWithdrawnFilterCriteria(self._session.getConference())
        f=filters.SimpleFilter(fc,self._sortingCrit)
        for contrib in f.apply(self._session.getContributionList()):
            wc=WContributionDisplayPosterItem(self._aw,contrib)
            html=wc.getHTML()
            cl.append("""<tr><td valign="top">%s</td></tr>"""%html)
        idHTML="""id <img src=%s border="0" alt="down">"""%quoteattr(str(Config.getInstance().getSystemIconURL("downArrow")))
        if self._sortingCrit.getField().getId()!="number":
            idHTML="""<a href=%s>id</a>"""%quoteattr(str(self._getURL("number")))
        #dateHTML="""date <img src=%s border="0" alt="down">"""%quoteattr(str(Config.getInstance().getSystemIconURL("downArrow")))
        #if self._sortingCrit.getField().getId()!="date":
        #    dateHTML="""<a href=%s>date</a>"""%quoteattr(str(self._getURL("date")))
        typeHTML="""type <img src=%s border="0" alt="down">"""%quoteattr(str(Config.getInstance().getSystemIconURL("downArrow")))
        if self._sortingCrit.getField().getId()!="type":
            typeHTML="""<a href=%s>type</a>"""%quoteattr(str(self._getURL("type")))
        spkHTML="""presenters <img src=%s border="0" alt="down">"""%quoteattr(str(Config.getInstance().getSystemIconURL("downArrow")))
        if self._sortingCrit.getField().getId()!="speaker":
            spkHTML="""<a href=%s>presenters</a>"""%quoteattr(str(self._getURL("speaker")))
        boardNumHTML="""board # <img src=%s border="0" alt="down">"""%quoteattr(str(Config.getInstance().getSystemIconURL("downArrow")))
        if self._sortingCrit.getField().getId()!="board_number":
            boardNumHTML="""<a href=%s>board #</a>"""%quoteattr(str(self._getURL("board_number")))
        return """
            <table cellspacing="0" cellpadding="5" width="100%%">
                <tr>
                    <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #5294CC; padding-right:10px;border-right:5px solid #FFFFFF">%s</td>
                    <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #5294CC; padding-right:10px;border-right:5px solid #FFFFFF">%s</td>
                    <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #5294CC; padding-right:10px;border-right:5px solid #FFFFFF">title</td>
                    <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #5294CC; padding-right:10px;border-right:5px solid #FFFFFF">%s</td>
                    <td nowrap class="titleCellFormat" style="border-bottom: 1px solid #5294CC; padding-right:10px;border-right:5px solid #FFFFFF">%s</td>
                </tr>
                %s
            </table>"""%(idHTML,typeHTML,spkHTML,boardNumHTML,"".join(cl))

    def _getColor(self,entry):
        bgcolor = "white"
        if isinstance(entry,schedule.LinkedTimeSchEntry):
            if isinstance(entry.getOwner(),conference.Contribution):
                bgcolor = entry.getOwner().getSession().getColor()
        elif isinstance(entry,schedule.BreakTimeSchEntry):
            bgcolor = entry.getColor()
        return bgcolor

    def _getMaterialHTML(self, contrib):
        lm=[]
        paper=contrib.getPaper()
        if paper is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="paper"><small> %s</small></a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(paper))),
                quoteattr(str(Config.getInstance().getSystemIconURL( "smallPaper" ))),
                self.htmlText("paper")))
        slides=contrib.getSlides()
        if slides is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="slides"><small> %s</small></a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(slides))),
                quoteattr(str(Config.getInstance().getSystemIconURL( "smallSlides" ))),
                self.htmlText("slides")))
        proceedings=None
        for mat in contrib.getMaterialList():
            if mat.getTitle().lower() == "proceedings":
                proceedings=mat
                break
        if proceedings is not None:
            lm.append("""<a href=%s><small> %s</small></a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(proceedings))),
                self.htmlText("proceedings")))
        video=contrib.getVideo()
        if video is None:
            for mat in contrib.getMaterialList():
               if mat.getTitle().lower().find("video") != -1:
                   video = mat
        if video is not None:
            lm.append("""<a href=%s><img src=%s border="0" alt="video"><small> %s</small></a>"""%(
                quoteattr(str(urlHandlers.UHMaterialDisplay.getURL(video))),
                quoteattr(str(Config.getInstance().getSystemIconURL( "smallVideo" ))),
                self.htmlText("video")))
        return ", ".join(lm)

    def _getContributionHTML(self,contrib):
        URL=urlHandlers.UHContributionDisplay.getURL(contrib)
        room = ""
        if contrib.getRoom() != None:
            room = "%s: "%contrib.getRoom().getName()
        speakerList = []
        for spk in contrib.getSpeakerList():
            spkcapt=spk.getDirectFullName()
            if spk.getAffiliation().strip() != "":
                spkcapt="%s (%s)"%(spkcapt, spk.getAffiliation())
            speakerList.append(spkcapt)
        speakers =""
        if speakerList != []:
            speakers = _("""<br><small> _("by") %s</small>""")%"; ".join(speakerList)
        linkColor=""
        if contrib.getSession().isTextColorToLinks():
            linkColor="color:%s"%contrib.getSession().getTextColor()
        return """<table width="100%%">
                        <tr>
                            <td width="100%%" align="center" style="color:%s">
                                [%s] <a href="%s" style="%s">%s</a>%s<br><small>(%s%s - %s)</small>
                            </td>
                            <td align="right" valign="top" nowrap style="color:%s">
                                %s
                            </td>
                        </tr>
                    </table>"""%(
                contrib.getSession().getTextColor(),contrib.getId(),URL,\
                linkColor, contrib.getTitle(),speakers,room,
                contrib.getAdjustedStartDate(self._tz).strftime("%H:%M"),
                contrib.getAdjustedEndDate(self._tz).strftime("%H:%M"),
                contrib.getSession().getTextColor(),
                self._getMaterialHTML(contrib))

    def _getBreakHTML(self,breakEntry):
        return """
                <font color="%s">%s<br><small>(%s - %s)</small></font>
                """%(\
                    breakEntry.getTextColor(),\
                    self.htmlText(breakEntry.getTitle()),\
                    self.htmlText(breakEntry.getAdjustedStartDate(self._tz).strftime("%H:%M")),\
                    self.htmlText(breakEntry.getAdjustedEndDate(self._tz).strftime("%H:%M")))

    def _getSchEntries(self):
        res=[]
        for slot in self._session.getSlotList():
            for entry in slot.getSchedule().getEntries():
                res.append(entry)
        return res

    def _getEntryHTML(self,entry):
        if isinstance(entry,schedule.LinkedTimeSchEntry):
            if isinstance(entry.getOwner(),conference.Contribution):
                return self._getContributionHTML(entry.getOwner())
        elif isinstance(entry,schedule.BreakTimeSchEntry):
            return self._getBreakHTML(entry)

    def _getTimeTableHTML(self):

        timeTable=timetable.TimeTable(self._session.getSchedule(),self._tz)
        sDate,eDate=self._session.getAdjustedStartDate(self._tz),self._session.getAdjustedEndDate(self._tz)
        timeTable.setStartDate(sDate)
        timeTable.setEndDate(eDate)
        tz = self._session.getTimezone()
        timeTable.mapEntryList(self._getSchEntries())
        daySch = []
        num_slots_in_hour=int(timedelta(hours=1).seconds/timeTable.getSlotLength().seconds)
        hourSlots,hourNeedsDisplay=[],False
        for day in timeTable.getDayList():
            hourSlots = []
            slotList=[]
            lastEntries=[]
            maxOverlap=day.getNumMaxOverlaping()
            width="100"
            if maxOverlap!=0:
                width=100/maxOverlap
            else:
                maxOverlap=1
            for slot in day.getSlotList():
                if slot.getAdjustedStartDate().minute==0:
                    if hourNeedsDisplay:
                        slotList.append("".join(hourSlots))
                    hourSlots,hourNeedsDisplay=[],False
                remColSpan=maxOverlap
                temp=[]
                for entry in slot.getEntryList():
                    hourNeedsDisplay=True
                    if len(slot.getEntryList()):
                        remColSpan=0
                    else:
                        remColSpan-=1
                    if entry in lastEntries:
                        continue
                    bgcolor=self._getColor(entry)
                    colspan=""
                    if not day.hasEntryOverlaps(entry):
                        colspan=""" colspan="%s" """%maxOverlap
                    temp.append("""<td valign="top" rowspan="%i" align="center" bgcolor="%s" width="%i%%"%s>%s</td>"""%(day.getNumSlots(entry),bgcolor,width,colspan,self._getEntryHTML(entry)))
                    lastEntries.append(entry)
                if remColSpan>0:
                    temp.append("""<td width="100%%" colspan="%i"></td>"""%(remColSpan))
                if slot.getAdjustedStartDate().minute==0:
                    slotHTML="""
                        <tr>
                            <td valign="top" rowspan="%s" bgcolor="white" width="40"><font color="gray" size="-1">%s</font></td>
                            %s
                        </tr>
                        """%(num_slots_in_hour,\
                                slot.getAdjustedStartDate().strftime("%H:%M"),\
                                "".join(temp))
                else:
                    if len(temp) == 0:
                        temp = ["<td></td>"]
                    slotHTML = """<tr>%s</tr>"""%"".join(temp)
                hourSlots.append(slotHTML)

                if slot == day.getSlotList()[-1]:
                    if hourNeedsDisplay:
                        slotList.append("".join(hourSlots))

            dayHTML="""
                <a name="%s">
                <table align="center" width="100%%">
                    <tr>
                        <td width="100%%">
                            <table align="center" border="0" width="100%%"
                                    celspacing="0" cellpadding="0" bgcolor="#E6E6E6">
                                <tr>
                                    <td colspan="%i" align="center" bgcolor="white"><b>%s</b></td>
                                </tr>
                                %s
                            </table>
                        </td>
                    </tr>
                </table>
                """%(day.getDate().strftime("%Y-%m-%d"),maxOverlap+2,
                        day.getDate().strftime("%A, %d %B %Y"),
                        "".join(slotList) )
            daySch.append(dayHTML)
        dayHTML = "<br>".join( daySch )
        return dayHTML

    def _getContribsHTML(self):
        self._createTabCtrl()
        if self._tabContribs.isActive():
            if self._session.getScheduleType()=="poster":
                html=self._getPosterContribListHTML()
            else:
                html=self._getContribListHTML()
        else:
            html=self._getTimeTableHTML()
        return WSessionTabControl(self._tabCtrl, self._aw).getHTML(html)

    def getVars(self):
        vars=wcomponents.WTemplated.getVars( self )

        vars["title"]=self.htmlText(self._session.getTitle())

        if self._session.getDescription():
            desc = self._session.getDescription().strip()
        else:
            desc = ""

        if desc!="":
            vars["description"]="""
                <tr>
                    <td colspan="2"><table width="100%%" cellpadding="0" cellspacing="0" class="tablepre"><tr><td><pre>%s</pre></td></tr></table></td>
                </tr>
                                """%desc
        else:
            vars["description"]=""

        tzUtil = timezoneUtils.DisplayTZ(self._aw,self._session.getOwner())
        tz = tzUtil.getDisplayTZ()
        sDate=self._session.getAdjustedStartDate(tz)
        eDate=self._session.getAdjustedEndDate(tz)
        if sDate.strftime("%d%b%Y")==eDate.strftime("%d%b%Y"):
            vars["dateInterval"]=sDate.strftime("%A %d %B %Y %H:%M")
        else:
            vars["dateInterval"]= _(""" _("from") %s  _("to") %s""")%(
                sDate.strftime("%A %d %B %Y %H:%M"),
                eDate.strftime("%A %d %B %Y %H:%M"))
        vars["location"]=""
        loc=self._session.getLocation()
        if loc is not None and loc.getName().strip()!="":
            vars["location"]="""<i>%s</i>"""%self.htmlText(loc.getName())
            if loc.getAddress().strip()!="":
                vars["location"]="""%s<pre>%s</pre>"""%(vars["location"],
                                                        loc.getAddress())
        room = self._session.getRoom()
        if room is not None:
            roomLink=linking.RoomLinker().getHTMLLink(room,loc)
            vars["location"]= _("""%s<br><small> _("Room"):</small> %s""")%(vars["location"],
                                                            roomLink)
        vars["location"]=self._getHTMLRow( _("Place"), vars["location"])
        sessionConvs=[]
        for convener in self._session.getConvenerList():
            sessionConvs.append("""<a href="mailto:%s">%s</a>"""%(convener.getEmail(),
                                        self.htmlText(convener.getFullName())))
        slotConvsHTML=""
        for entry in self._session.getSchedule().getEntries():
            slot=entry.getOwner()
            l=[]
            for convener in slot.getOwnConvenerList():
                l.append("""<a href="mailto:%s">%s</a>"""%(convener.getEmail(),
                                        self.htmlText(convener.getFullName())))
            if len(l)>0:
                slotConvsHTML+="""
                    <tr>
                        <td valign="top">%s (<small>%s-%s</small>):</td>
                        <td>%s</td>
                    </tr>
                      """%(self.htmlText(slot.getTitle()),
                      slot.getAdjustedStartDate().strftime("%d-%b-%y %H:%M"),
                      slot.getAdjustedEndDate().strftime("%d-%b-%y %H:%M"),
                      "; ".join(l))
        convs=""
        if len(sessionConvs)>0 or slotConvsHTML.strip()!="":
            convs="""
                <table>
                    <tr>
                        <td valign="top" colspan="2">%s</td>
                    </tr>
                    %s
                </table>"""%("<br>".join(sessionConvs),slotConvsHTML)
        vars["conveners"]=self._getHTMLRow( _("Conveners"),convs)
        lm = []
        for material in self._session.getAllMaterialList():
            url=urlHandlers.UHMaterialDisplay.getURL(material)
            lm.append(wcomponents.WMaterialDisplayItem().getHTML(self._aw,material,url))
        vars["material"] = self._getHTMLRow( _("Material"), "<br>".join( lm ) )
        vars["contribs"]= ""
        if self._session.getContributionList() != []:
            vars["contribs"]=self._getContribsHTML()
        vars["PDFIcon"]=quoteattr(str(Config.getInstance().getSystemIconURL("print")))
        url=urlHandlers.UHConfTimeTablePDF.getURL(self._session.getConference())
        url.addParam("showSessions",self._session.getId())
        if self._session.getScheduleType()=="poster":
            if self._sortingCrit is not None and \
                    self._sortingCrit.getField() is not None:
                url.addParam("sortBy",self._sortingCrit.getField().getId())
        vars["PDFURL"]=quoteattr(str(url))
        return vars


# TODO: These classes are actually the same, no?  (Pedro)

class WSessionDisplayFull(WSessionDisplayBase):
    pass


class WSessionDisplayMin(WSessionDisplayBase):
    pass


class WSessionDisplay:

    def __init__(self,aw,session):
        self._aw = aw
        self._session = session

    def getHTML(self,params={}):
        if self._session.canAccess( self._aw ):
            c=WSessionDisplayFull(self._aw,self._session,params["activeTab"],
                    params.get("sortingCrit",None))
            return c.getHTML( params )
        if self._session.canView( self._aw ):
            c = WSessionDisplayMin(self._aw,self._session,params["activeTab"],
                    params.get("sortingCrit",None))
            return c.getHTML( params )
        return ""


class WPSessionDisplay( WPSessionDefaultDisplayBase ):
    navigationEntry = navigation.NESessionDisplay

    def _getBody(self,params):
        wc=WSessionDisplay(self._getAW(),self._session)
        return wc.getHTML({"activeTab":params["activeTab"],
                            "sortingCrit":params.get("sortingCrit",None)})

    def _defineToolBar(self):
        edit=wcomponents.WTBItem( _("manage this session"),
            icon=Config.getInstance().getSystemIconURL("modify"),
            actionURL=urlHandlers.UHSessionModification.getURL(self._session),
            enabled=self._session.canModify(self._getAW()) or \
                    self._session.canCoordinate(self._getAW()))
        url=urlHandlers.UHConfTimeTablePDF.getURL(self._session.getConference())
        url.addParam("showSessions",self._session.getId())
        pdf=wcomponents.WTBItem( _("get PDF of this session"),
            icon=Config.getInstance().getSystemIconURL("pdf"),
            actionURL=url)
        ical=wcomponents.WTBItem( _("get ICal of this session"),
            icon=Config.getInstance().getSystemIconURL("ical"),
            actionURL=urlHandlers.UHSessionToiCal.getURL(self._session))
        self._toolBar.addItem(edit)
        self._toolBar.addItem(pdf)
        self._toolBar.addItem(ical)


class WPSessionModifBase( WPConferenceModifBase ):

    def __init__(self, rh, session):
        WPConferenceModifBase.__init__(self, rh, session.getConference())
        self._session = session

    def _setActiveSideMenuItem( self ):
        self._timetableMenuItem.setActive()

    def _createTabCtrl( self ):
        type = self._session.getConference().getType()
        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab( "main", _("Main"), \
                urlHandlers.UHSessionModification.getURL( self._session ) )
        self._tabContribs=self._tabCtrl.newTab( "contribs", _("Contributions"), \
                urlHandlers.UHSessionModContribList.getURL(self._session) )
        self._tabTimetable=self._tabCtrl.newTab( "sessionTimetable", _("Session timetable"), \
                urlHandlers.UHSessionModifSchedule.getURL(self._session) )
        self._tabComm = self._tabCtrl.newTab( "comment", _("Comment"), \
                urlHandlers.UHSessionModifComm.getURL( self._session ) )
        self._tabMaterials = self._tabCtrl.newTab( "materials", _("Files"), \
                urlHandlers.UHSessionModifMaterials.getURL( self._session ) )
        self._tabAC = self._tabCtrl.newTab( "ac", _("Protection"), \
                urlHandlers.UHSessionModifAC.getURL( self._session ) )

        canModify=self._session.canModify(self._getAW())
        self._tabAC.setEnabled(canModify)
        self._tabTools = self._tabCtrl.newTab( "tools", _("Tools"), \
                urlHandlers.UHSessionModifTools.getURL( self._session ) )
        self._tabTools.setEnabled(canModify)
        self._setActiveTab()
        self._setupTabCtrl()
        if type != "conference":
            self._tabContribs.disable()

    def _setActiveTab( self ):
        pass

    def _setupTabCtrl(self):
        pass

    def _getNavigationDrawer(self):
        pars = {"target": self._session, "isModif": True }
        return wcomponents.WNavigationDrawer( pars, bgColor="white" )

    def _getPageContent( self, params ):
        self._createTabCtrl()

        banner = wcomponents.WTimetableBannerModif(self._session).getHTML()
        body = wcomponents.WTabControl( self._tabCtrl, self._getAW() ).getHTML( self._getTabContent( params ) )
        return banner + body


class WSessionModifClosed(wcomponents.WTemplated):

    def __init__(self):
        pass

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["closedIconURL"] = Config.getInstance().getSystemIconURL("closed")
        return vars

class WSessionModifMainType(wcomponents.WTemplated):

    def __init__(self):
        pass

    def getVars( self ):
        vars=wcomponents.WTemplated.getVars(self)
        l=[]
        currentTTType=vars.get("tt_type",conference.SlotSchTypeFactory.getDefaultId())
        for i in conference.SlotSchTypeFactory.getIdList():
            sel=""
            if i==currentTTType:
                sel=" selected"
            l.append("""<option value=%s%s>%s</option>"""%(quoteattr(str(i)),
                        sel,self.htmlText(i)))
        vars["tt_types"]="".join(l)
        return vars

class WSessionModifMainCode(wcomponents.WTemplated):

    def __init__(self):
        pass

    def getVars( self ):
        vars=wcomponents.WTemplated.getVars(self)
        vars["code"]=str(vars.get("code",""))
        return vars

class WSessionModifMainColors(wcomponents.WTemplated):

    def __init__(self):
        pass

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        return vars

class WSessionModifMain(wcomponents.WTemplated):

    def __init__( self, session, mfRegistry ):
        self._session = session
        self._mfr = mfRegistry

    def _getConvenersHTML(self):
        res=[]
        for conv in self._session.getConvenerList():
            url=urlHandlers.UHSessionModConvenerEdit.getURL(conv)
            res.append("""
                <input type="checkbox" name="selConv" value=%s> <a href=%s>%s</a>
                """%(quoteattr(str(conv.getId())),\
                    quoteattr(str(url)), \
                    self.htmlText(conv.getFullName())))
        return "<br>".join(res)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["addMaterialURL"]=urlHandlers.UHSessionAddMaterial.getURL(self._session)
        vars["removeMaterialsURL"]=urlHandlers.UHSessionRemoveMaterials.getURL()

        newConvenerURL = urlHandlers.UHSessionDataModificationNewConvenerCreate.getURL(self._session)
        vars["newConvenerURL"] = newConvenerURL
        searchConvenerURL = urlHandlers.UHSessionDataModificationNewConvenerSearch.getURL(self._session)
        vars["searchConvenerURL"] = searchConvenerURL
        vars["remConvenersURL"]=quoteattr(str(urlHandlers.UHSessionModConvenersRem.getURL(self._session)))
        vars["dataModificationURL"]=quoteattr(str(urlHandlers.UHSessionDataModification.getURL(self._session)))
        vars["code"]=self.htmlText(self._session.getCode())
        vars["title"]=self._session.getTitle()
        if isStringHTML(self._session.getDescription()):
            vars["description"] = self._session.getDescription()
        else:
            vars["description"] = """<table class="tablepre"><tr><td><pre>%s</pre></td></tr></table>""" % self._session.getDescription()
        vars["place"]=""
        place=self._session.getLocation()
        if place is not None:
            vars["place"] = "%s<br><pre>%s</pre>"%(\
                                            self.htmlText(place.getName()),
                                            self.htmlText(place.getAddress()))
        room=self._session.getRoom()
        if room is not None:
            vars["place"]+="<i>Room:</i> %s"%self.htmlText(room.getName())
        vars["startDate"],vars["endDate"],vars["duration"]="","",""
        if self._session.getAdjustedStartDate() is not None:
            tz = self._session.getTimezone()
            vars["startDate"]=self.htmlText(self._session.getAdjustedStartDate().strftime("%A %d %B %Y %H:%M"))
            vars["endDate"]=self.htmlText(self._session.getAdjustedEndDate().strftime("%A %d %B %Y %H:%M"))
        vars["conveners"]=self._getConvenersHTML()
        vars["bgcolor"] = self._session.getColor()
        vars["textcolor"] = self._session.getTextColor()
        vars["entryDuration"]=self.htmlText((datetime(1900,1,1)+self._session.getContribDuration()).strftime("%Hh%M'"))
        vars["tt_type"]=self.htmlText(self._session.getScheduleType())
        type = self._session.getConference().getType()
        if type == "conference":
            vars["Type"]=WSessionModifMainType().getHTML(vars)
            vars["Colors"]=WSessionModifMainColors().getHTML(vars)
            vars["Code"]=WSessionModifMainCode().getHTML(vars)
            vars["Rowspan"]=9
        else:
            vars["Type"]=""
            vars["Colors"]=""
            vars["Code"]=""
            vars["Rowspan"]=6
        return vars


class WPSessionModification( WPSessionModifBase ):

    def _getTabContent( self, params ):
        comp=WSessionModifMain(self._session,materialFactories.SessionMFRegistry())
        return comp.getHTML()

class WPSessionModificationClosed( WPSessionModifBase ):

    def _createTabCtrl( self ):
        self._tabCtrl = wcomponents.TabControl()
        self._tabMain = self._tabCtrl.newTab( "main",_("Main"), "")
        self._setActiveTab()

    def _getTabContent( self, params ):
        comp=WSessionModifClosed()
        return comp.getHTML()

#------------------------------------------------------------------------------------

class WPSessionDataModification(WPSessionModification):

    def _getTabContent(self,params):
        title="Edit session data"
        p=wcomponents.WSessionModEditData(self._session.getConference(),self._getAW(),title)
        params["postURL"]=urlHandlers.UHSessionDataModification.getURL(self._session)
        params["colorChartIcon"]=Config.getInstance().getSystemIconURL("colorchart")
        urlbg=urlHandlers.UHSimpleColorChart.getURL()
        urlbg.addParam("colorCodeTarget", "backgroundColor")
        urlbg.addParam("colorPreviewTarget", "backgroundColorpreview")
        params["bgcolorChartURL"]=urlbg
        params["bgcolor"] = self._session.getColor()
        urltext=urlHandlers.UHSimpleColorChart.getURL()
        urltext.addParam("colorCodeTarget", "textColor")
        urltext.addParam("colorPreviewTarget", "textColorpreview")
        params["textcolorChartURL"]=urltext
        params["textcolor"] = self._session.getTextColor()
        params["textColorToLinks"]=""
        if self._session.isTextColorToLinks():
            params["textColorToLinks"]="checked=\"checked\""

        #wconvener = wcomponents.WAddPersonModule("convener")
        #params["convenerDefined"] = self._getDefinedDisplayList("convener")
        #params["convenerOptions"] = ""
        #params["convener"] = wconvener.getHTML(params)
        params["convener"] = ""
        return p.getHTML(params)

    def _getDefinedDisplayList(self, typeName):
         list = self._session.getConvenerList()
         if list is None :
             return ""
         html = []
         counter = 0
         for person in list :
             text = """
                 <tr>
                     <td width="5%%"><input type="checkbox" name="%ss" value="%s"></td>
                     <td>&nbsp;%s</td>
                 </tr>"""%(typeName,counter,person.getFullName())
             html.append(text)
             counter = counter + 1
         return """
             """.join(html)

#---------------------------------------------------------------------------

class WPSessionDataModificationConvenerSelect( WPSessionModifBase):

    #def _setActiveTab( self ):
    #    self._tabContribList.setActive()

    def _getTabContent( self, params ):
        searchAction = str(self._rh.getCurrentURL())
        newButtonAction = params["newButtonAction"]
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        p = wcomponents.WComplexSelection(self._conf,searchAction,forceWithoutExtAuth=searchLocal)
        return p.getHTML(params)

#---------------------------------------------------------------------------

class WPSessionDataModificationConvenerNew(WPSessionModifBase):

    #def _setActiveTab( self ):
    #    self._tabContribList.setActive()

    def _getTabContent( self, params ):
        p = wcomponents.WNewPerson()

        if params.get("formTitle",None) is None :
            params["formTitle"] =_("Define new convener")
        if params.get("titleValue",None) is None :
            params["titleValue"] = ""
        if params.get("surNameValue",None) is None :
            params["surNameValue"] = ""
        if params.get("nameValue",None) is None :
            params["nameValue"] = ""
        if params.get("emailValue",None) is None :
            params["emailValue"] = ""
        if params.get("addressValue",None) is None :
            params["addressValue"] = ""
        if params.get("affiliationValue",None) is None :
            params["affiliationValue"] = ""
        if params.get("phoneValue",None) is None :
            params["phoneValue"] = ""
        if params.get("faxValue",None) is None :
            params["faxValue"] = ""


        params["disabledRole"] = False
        params["roleDescription"] = _(""" _("Coordinator")<br> _("Manager")""")
        if params.has_key("submissionControlValue") :
            params["roleValue"] = _(""" <input type="checkbox" name="coordinatorControl" checked> _("Give coordinator rights to the convener").<br>
                                      <input type="checkbox" name="managerControl" checked> _("Give management rights to the convener").""")
        else:
            params["roleValue"] = _(""" <input type="checkbox" name="coordinatorControl"> _("Give coordinator rights to the convener").<br>
                                      <input type="checkbox" name="managerControl"> _("Give management rights to the convener").""")
        params["disabledNotice"] = True
        params["noticeValue"] = _("""<i><font color="black"><b> _("Note"): </b></font> _("If this person does not already have
         an Indico account, he or she will be sent an email asking to create an account. After the account creation the
         user will automatically be given coordinator rights").</i>""")


        if params.get("formAction",None) is None :
            formAction = urlHandlers.UHSessionDataModificationPersonAdd.getURL(self._conf)
            formAction.addParam("sessionId",self._session.getId())
            formAction.addParam("orgin","new")
            formAction.addParam("typeName","convener")
            params["formAction"] = formAction

        return p.getHTML(params)

#---------------------------------------------------------------------------

class WPModEditDataConfirmation(WPSessionModification):

    def _getTabContent(self,params):
        wc=wcomponents.WConfirmation()
        msg= _("""You have selected to CHANGE THIS SESSION SCHEDULE TYPE from %s to %s, if you continue any contribution scheduled within any slot of the current session will be unscheduled, are you sure you want to continue?""")%(self._session.getScheduleType(),params["tt_type"])
        url=urlHandlers.UHSessionDataModification.getURL(self._session)
        return wc.getHTML(msg,url,params)


class WPModConvenerNew(WPSessionModification):

    def _getTabContent(self,params):
        caption= _("Adding a new convener")
        wc=wcomponents.WConfModParticipEdit(title=caption)
        params["postURL"]=urlHandlers.UHSessionModConvenerNew.getURL(self._session)
        params["addToManagersList"]= _("""
                                    <tr>
                                        <td nowrap class="titleCellTD">
                                            <span class="titleCellFormat"> _("Specific rights")</span>
                                        </td>
                                        <td bgcolor="white" width="100%%" valign="top" class="blacktext">
                                            <input type="radio" name="specialRights" value="none" checked> _("Do not give specific rights").<br>
                                            <input type="radio" name="specialRights" value="manager"> _("Give session manager rights to the convener").<br>
                                            <input type="radio" name="specialRights" value="coordinator"> _("Give session coordinator rights to the convener").<br><br><i><font color="black"><b> _("Note"): </b></font> _("If this person does not already have an Indico account, he or she will be sent an email asking to create an account. After the account creation the user will automatically be given the specific rights").</i>
                                        </td>
                                    </tr>
                                    """)
        return wc.getHTML( params )



class WPModConvenerEdit(WPSessionModification):

##    def _getTabContent(self,params):
##        caption="Edit convener data"
##        conv=params["convener"]
##        wc=wcomponents.WConfModParticipEdit(part=conv,title=caption)
##        params["postURL"]=urlHandlers.UHSessionModConvenerEdit.getURL(conv)
##        params["addToManagersList"]=""
##        return wc.getHTML(params)

    def _getTabContent(self,params):
        p = wcomponents.WNewPerson()
        conv = params["convener"]
        params["formTitle"] =  _("Define new convener")
        params["titleValue"] = conv.getTitle()
        params["surNameValue"] = conv.getFamilyName()
        params["nameValue"] = conv.getFirstName()
        params["emailValue"] = conv.getEmail()
        params["addressValue"] = conv.getAddress()
        params["affiliationValue"] = conv.getAffiliation()
        params["phoneValue"] = conv.getPhone()
        params["faxValue"] = conv.getFax()

        params["disabledRole"] = False
        params["roleDescription"] =  _(""" _("Coordinator")<br> _("Manager")""")
        session = conv.getSession()
        av = user.AvatarHolder().match({"email":conv.getEmail()})
        params["disabledNotice"] = True
        coordValue =  _("""<input type="checkbox" name="coordinatorControl"> _("Give coordinator rights to the convener").""")
        if (av and av[0] in session.getCoordinatorList()) or conv.getEmail() in session.getCoordinatorEmailList():
            coordValue = _("""The convener is already a coordinator""")
        else:
            params["disabledNotice"] = False

        managerValue =  _("""<input type="checkbox" name="managerControl"> _("Give management rights to the convener").""")
        if (av and av[0] in session.getManagerList() ) or conv.getEmail() in session.getAccessController().getModificationEmail():
            managerValue = _("""The convener is already a manager""")
        else:
            params["disabledNotice"] = False

        params["roleValue"] = """ %s<br>
                                  %s"""%(coordValue, managerValue)

        params["noticeValue"] =  _("""<i><font color="black"><b> _("Note"): </b></font> _("If this person does not already have
         an Indico account, he or she will be sent an email asking to create an account. After the account creation the
         user will automatically be given coordinator/manager rights").</i>""")

        formAction = urlHandlers.UHSessionModConvenerEdit.getURL(conv)
        formAction.addParam("orgin","new")
        formAction.addParam("typeName","convener")
        params["formAction"] = formAction

        return p.getHTML(params)



class WPSessionAddMaterial( WPSessionModification ):

    def __init__( self, rh, session, mf ):
        WPSessionModification.__init__( self, rh, session )
        self._mf = mf

    def _getTabContent( self, params ):
        if self._mf:
            comp = self._mf.getCreationWC( self._session )
        else:
            comp = wcomponents.WMaterialCreation( self._session )
        pars = { "postURL": urlHandlers.UHSessionPerformAddMaterial.getURL() }
        return comp.getHTML( pars )


class WSessionModPlainTTDay(wcomponents.WTemplated):

    def __init__(self,aw,day,session):
        self._aw=aw
        self._day=day
        self._session=session

    def _getContribHTML(self,contrib):
        duration=(datetime(1900,1,1)+contrib.getDuration()).strftime("%Hh%M'")
        speakers=[]
        for spk in contrib.getSpeakerList():
            speakers.append(self.htmlText("%s"%spk.getFullName()))
        url=urlHandlers.UHContributionModification.getURL(contrib)
        urlEdit=urlHandlers.UHSessionModSchEditContrib.getURL(contrib)
        editIconURL=Config.getInstance().getSystemIconURL("modify")
        return """
            <tr>
                <td valign="top" nowrap><input type="checkbox" name="schEntryId" value=%s></td>
                <td valign="top" nowrap>%s</td>
                <td valign="top" nowrap>(%s)</td>
                <td valign="top" nowrap><a href=%s><img src=%s border="0" alt=""></a></td>
                <td width="100%%" valign="top">
                    <table width="100%%" cellpadding="0" cellspacing="0">
                        <tr>
                            <td width="100%%" valign="top">
                                [%s] <a href=%s>%s</a>
                            </td>
                            <td nowrap align="right" valign="top">
                                %s
                            </td>
                        </tr cellpadding="0" cellspacing="0">
                    </table>
                </td>
            </tr>
            <tr>
                <td colspan="5" nowrap valign="top" style="border-top: 1px solid">&nbsp;</td>
            </tr>
                """%( contrib.getSchEntry().getId(),
                        contrib.getAdjustedStartDate().strftime("%H:%M"),
                        duration,quoteattr(str(urlEdit)),
                        quoteattr(str(editIconURL)),
                        self.htmlText(contrib.getId()),
                        quoteattr(str(url)),
                        self.htmlText(contrib.getTitle()),
                        "<br>".join(speakers))

    def _getBreakHTML(self,breakEntry):
        duration=(datetime(1900,1,1)+breakEntry.getDuration()).strftime("%Hh%M")
        url=urlHandlers.UHSessionModifyBreak.getURL(breakEntry)
        urlEdit=urlHandlers.UHSessionModifyBreak.getURL(breakEntry)
        editIconURL=Config.getInstance().getSystemIconURL("modify")
        return """
            <tr>
                <td valign="top" nowrap><input type="checkbox" name="schEntryId" value=%s></td>
                <td valign="top" nowrap>%s</td>
                <td valign="top" nowrap>(%s)</td>
                <td valign="top" nowrap><a href=%s><img src=%s border="0" alt=""></a></td>
                <td width="100%%" valign="top" align="center">
                    <a href=%s>%s</a>
                </td>
            </tr>
            <tr>
                <td colspan="5" nowrap valign="top" style="border-top: 1px solid">&nbsp;</td>
            </tr>
                """%(breakEntry.getId(),
                        breakEntry.getAdjustedStartDate().strftime("%H:%M"),
                        duration,quoteattr(str(urlEdit)),
                        quoteattr(str(editIconURL)),
                        quoteattr(str(url)),
                        self.htmlText(breakEntry.getTitle()))

    def _getSlotHTML(self,slot):
        caption = ""
        if slot.getRoom() is not None:
            caption=slot.getRoom().getName()
        if slot.getTitle().strip() != "":
            caption = "%s (%s)"%(self.htmlText(slot.getTitle()),self.htmlText(caption))
        duration=""
        if (datetime(1900,1,1)+slot.getDuration()).minute>0:
            duration="%s'"%(datetime(1900,1,1)+slot.getDuration()).minute
        if (datetime(1900,1,1)+slot.getDuration()).hour>0:
            duration="%sh%s"%((datetime(1900,1,1)+slot.getDuration()).hour,duration)
        if duration!="":
            duration="(%s)"%duration
        entries=[]
        at=timedelta(0,0,0)
        for entry in slot.getSchedule().getEntries():
            if isinstance(entry,schedule.LinkedTimeSchEntry) and \
                    isinstance(entry.getOwner(),conference.Contribution):
                entries.append(self._getContribHTML(entry.getOwner()))
            elif isinstance(entry,schedule.BreakTimeSchEntry):
                entries.append(self._getBreakHTML(entry))
            at+=entry.getDuration()
        addContribURL=urlHandlers.UHSessionModScheduleAddContrib.getURL(slot)

        orginURL = urlHandlers.UHSessionModifSchedule.getURL(self._session.getOwner())
        orginURL.addParam("sessionId", self._session.getId())
        newContribURL = urlHandlers.UHConfModScheduleNewContrib.getURL(self._session.getOwner())
        newContribURL.addParam("sessionId", self._session.getId())
        newContribURL.addParam("slotId", slot.getId())
        newContribURL.addParam("orginURL",orginURL)

        addBreakURL=urlHandlers.UHSessionAddBreak.getURL(slot)
        delSlotURL=urlHandlers.UHSessionModSlotRem.getURL(slot)
        editSlotURL=urlHandlers.UHSessionModSlotEdit.getURL(slot)
        delContribsURL=urlHandlers.UHSessionDelSchItems.getURL(slot)
        urlCompSlot = urlHandlers.UHSessionModSlotCalc.getURL(slot)
        if slot.getContribDuration() is None or slot.getContribDuration()==timedelta(0):
            ded=slot.getSession().getContribDuration()
        else:
            ded=slot.getContribDuration()
        nat=slot.getDuration()-at
        numEntries=len(entries)
        ree=0
        if ded!=0 and ded.seconds != 0:
            ree=int(nat.seconds/ded.seconds)
        linkColor=""
        if self._session.isTextColorToLinks():
            linkColor="color:%s"%self._session.getTextColor()
        editSlotLink,delSlotLink="",""
        if self._session.canModify(self._aw) or self._session.canCoordinate(self._aw, "unrestrictedSessionTT"):
            editSlotLink="""<input type="submit" value="delete" onClick="self.location.href='%s';return false;" class="smallbtn">"""%str(delSlotURL)
            delSlotLink="""<input type="submit" value="edit" onClick="self.location.href='%s';return false;" class="smallbtn">"""%str(editSlotURL)

        convs=""
        l=[]
        if slot.getConvenerList() == []:
            for conv in self._session.getConvenerList():
                l.append("""%s"""%(self.htmlText(conv.getFullName())))
        else:
            for conv in slot.getConvenerList():
                l.append("""%s"""%(self.htmlText(conv.getFullName())))
        if len(l)>0:
            convs="Conveners: %s"%"; ".join(l)
        return  _("""
            <a name="slot%s"/>
            <table width="90%%" align="center" border="0"
                                        style="border-left: 1px solid #777777">
                <tr>
                    <td class="groupTitle" style="background: %s">
                        <table>
                            <tr>
                                <td nowrap class="groupTitle" style="background:%s;color: %s">
                                    %s-%s %s
                                </td>
                                <td width="100%%" align="center" class="groupTitle" style="background:%s;color: %s">
                                    %s
                                </td>
                                <td align="right" nowrap style="letter-spacing: 0px">
                                    <input type="submit" value="_("add contribution")" onClick="self.location.href='%s';return false;" class="smallbtn">
                                    <input type="submit" value="_("new contribution")" onClick="self.location.href='%s';return false;" class="smallbtn">
                                    <input type="submit" value="_("new break")" onClick="self.location.href='%s';return false;" class="smallbtn">
                                    %s %s
                                    <input type="submit" value="_("reschedule")" onClick="self.location.href='%s';return false;" class="smallbtn">
                                </td>
                            </tr>
                            <tr>
                                <td colspan="3" style="letter-spacing: 0px;background:%s;color:%s">
                                    <small>%s</small>
                                </td>
                            </tr>
                            <tr>
                                <td colspan="3" style="letter-spacing: 0px; color:%s">
                                    <small>NAT:%s - AT:%s - #E:%s - DED:%s - #REE:%s</small>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <form action=%s method="POST">
                <tr>
                    <td>
                        <table width="100%%" align="center">
                            %s
                        </table>
                    </td>
                </tr>
                <tr>
                    <td>
                        <table>
                            <tr>
                                <td><input type="submit" class="btn" value="_("remove selected")"></td>
                            </tr>
                        </table>
                    </td>
                </tr>
                </form>
            </table>
                """)%( slot.getId(),self._session.getColor(), self._session.getColor(), self._session.getTextColor(), \
                        slot.getAdjustedStartDate().strftime("%H:%M"), \
                        slot.getAdjustedEndDate().strftime("%H:%M"), \
                        duration,self._session.getColor(),self._session.getTextColor(),caption, \
                        str(addContribURL), \
                        str(newContribURL), \
                        str(addBreakURL), \
                        editSlotLink,delSlotLink, \
                        quoteattr(str(urlCompSlot)), linkColor, \
                        self._session.getTextColor(), convs,self._session.getTextColor(), \
                        (datetime(1900,1,1)+nat).strftime("%Hh%M'"),(datetime(1900,1,1)+at).strftime("%Hh%M'"), \
                        numEntries,(datetime(1900,1,1)+ded).strftime("%Hh%M'"), \
                        ree, \
                        quoteattr(str(delContribsURL)), \
                        "".join(entries))

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["day"]=self._day.strftime("%A, %d %B %Y")
        tz = self._session.getTimezone()
        sDate=timezone(tz).localize(datetime(self._day.year,self._day.month,self._day.day,0,0))
        eDate=timezone(tz).localize(datetime(self._day.year,self._day.month,self._day.day,23,59))
        res=[]
        for slotEntry in self._session.getSchedule().getEntries():
            if slotEntry.getAdjustedStartDate()>eDate:
                break
            if slotEntry.getAdjustedEndDate()>=sDate and \
                                slotEntry.getAdjustedStartDate()<=eDate:
                res.append(self._getSlotHTML(slotEntry.getOwner()))
        vars["slots"]="<br>".join(res)
        urlNewSlot=urlHandlers.UHSessionModSlotNew.getURL(self._session)
        urlNewSlot.addParam("slotDate",self._day.strftime("%d-%m-%Y"))
        vars["newSlotURL"]=quoteattr(str(urlNewSlot))
        vars["newSlotBtn"]="&nbsp;"
        if self._session.canModify(self._aw) or self._session.canCoordinate(self._aw, "unrestrictedSessionTT"):
            if self._session.getConference().getEnableSessionSlots() :
                vars["newSlotBtn"]= _("""<input type="submit" class="btn" value="_("new slot")">""")
        vars["fitToInnerSlots"] = "&nbsp;"
        if self._session.getConference().getEnableSessionSlots() :
            vars["fitToInnerSlots"] = _("""<input type="submit" class="btn" value="_("fit to inner slots")">""")
        vars["start_date"] = self._session.getAdjustedStartDate().strftime("%a %d %b %Y %H:%M")
        vars["end_date"] = self._session.getAdjustedEndDate().strftime("%a %d %b %Y %H:%M")
        vars["editURL"] = quoteattr(str(urlHandlers.UHSessionModFit.getURL(self._session)))
        return vars


class WSessionModPosterTTDay(wcomponents.WTemplated):

    def __init__(self,aw,day,session):
        self._aw=aw
        self._day=day
        self._session=session

    def _getContribHTML(self,contrib):
        #duration=(datetime(1900,1,1)+contrib.getDuration()).strftime("%Hh%M'")
        speakers=[]
        for spk in contrib.getSpeakerList():
            speakers.append(self.htmlText("%s"%spk.getFullName()))
        url=urlHandlers.UHContributionModification.getURL(contrib)
        urlEdit=urlHandlers.UHSessionModSchEditContrib.getURL(contrib)
        editIconURL=Config.getInstance().getSystemIconURL("modify")
        return """
            <tr>
                <td valign="top" nowrap><input type="checkbox" name="schEntryId" value=%s></td>
                <td valign="top" nowrap>%s</td>
                <td valign="top" nowrap><a href=%s><img src=%s border="0" alt=""></a></td>
                <td width="100%%" valign="top">
                    <table width="100%%" cellpadding="0" cellspacing="0">
                        <tr>
                            <td width="100%%" valign="top">
                                [%s] <a href=%s>%s</a>
                            </td>
                            <td nowrap align="right" valign="top">
                                %s
                            </td>
                        </tr cellpadding="0" cellspacing="0">
                    </table>
                </td>
            </tr>
            <tr>
                <td colspan="5" nowrap valign="top" style="border-top: 1px solid">&nbsp;</td>
            </tr>
                """%( contrib.getSchEntry().getId(),
                        self.htmlText(contrib.getBoardNumber()),
                        quoteattr(str(urlEdit)),
                        quoteattr(str(editIconURL)),
                        self.htmlText(contrib.getId()),
                        quoteattr(str(url)),
                        self.htmlText(contrib.getTitle()),
                        "<br>".join(speakers))

    def _getSlotHTML(self,slot):
        caption = ""
        if slot.getRoom() is not None:
            caption=slot.getRoom().getName()
        if slot.getTitle().strip() != "":
            caption = "%s (%s)"%(self.htmlText(slot.getTitle()),self.htmlText(caption))
        duration=""
        if (datetime(1900,1,1)+slot.getDuration()).minute>0:
            duration="%s'"%(datetime(1900,1,1)+slot.getDuration()).minute
        if (datetime(1900,1,1)+slot.getDuration()).hour>0:
            duration="%sh%s"%((datetime(1900,1,1)+slot.getDuration()).hour,duration)
        if duration!="":
            duration="(%s)"%duration
        entries=[]
        for entry in slot.getSchedule().getEntries():
            if isinstance(entry,schedule.LinkedTimeSchEntry) and \
                    isinstance(entry.getOwner(),conference.Contribution):
                entries.append(self._getContribHTML(entry.getOwner()))
        addContribURL=urlHandlers.UHSessionModScheduleAddContrib.getURL(slot)

        orginURL = urlHandlers.UHSessionModifSchedule.getURL(self._session.getOwner())
        orginURL.addParam("sessionId", self._session.getId())
        newContribURL = urlHandlers.UHConfModScheduleNewContrib.getURL(self._session.getOwner())
        newContribURL.addParam("sessionId", self._session.getId())
        newContribURL.addParam("slotId", slot.getId())
        newContribURL.addParam("orginURL",orginURL)

        delSlotURL=urlHandlers.UHSessionModSlotRem.getURL(slot)
        editSlotURL=urlHandlers.UHSessionModSlotEdit.getURL(slot)
        delContribsURL=urlHandlers.UHSessionDelSchItems.getURL(slot)
        numEntries=len(entries)
        linkColor=""
        if self._session.isTextColorToLinks():
            linkColor="color:%s"%self._session.getTextColor()
        editSlotLink,delSlotLink="",""
        if self._session.canModify(self._aw) or self._session.canCoordinate(self._aw, "unrestrictedSessionTT"):
            editSlotLink="""<input type="submit" value="delete" onClick="self.location.href='%s';return false;" class="smallbtn">"""%str(delSlotURL)
            delSlotLink="""<input type="submit" value="edit" onClick="self.location.href='%s';return false;" class="smallbtn">"""%str(editSlotURL)
        convs=""
        l=[]
        if slot.getConvenerList() == []:
            for conv in slot.getSession().getConvenerList():
                l.append("""%s"""%(self.htmlText(conv.getFullName())))
        else:
            for conv in slot.getConvenerList():
                l.append("""%s"""%(self.htmlText(conv.getFullName())))
        if len(l)>0:
            convs="""<span style="letter-spacing: 0px">Conveners: %s</span>"""%"; ".join(l)
        return  _("""
            <a name="slot%s"/>
            <table width="90%%" align="center" border="0"
                                        style="border-left: 1px solid #777777">
                <tr>
                    <td class="groupTitle" style="background-color: %s">
                        <table>
                            <tr>
                                <td nowrap class="groupTitle" style="background-color: %s; color: %s">
                                    %s-%s %s
                                </td>
                                <td width="100%%" align="center" class="groupTitle" style="background-color: %s; color: %s">
                                    %s
                                </td>
                                <td align="right" nowrap style="letter-spacing: 0px">
                                    <input type="submit" value="_("add contribution")" onClick="self.location.href='%s';return false;" class="smallbtn">
                                    <input type="submit" value="_("new contribution")" onClick="self.location.href='%s';return false;" class="smallbtn">
                                    %s %s
                                </td>
                            </tr>
                            <tr>
                                <td colspan="3" style="color:%s">%s</td>
                            </tr>
                            <tr>
                                <td colspan="3" style="color:%s">%s  _("entries")</td>
                            </tr>
                        </table>
                    </td>
                </tr>
                <form action=%s method="POST">
                <tr>
                    <td>
                        <table width="100%%" align="center">
                            %s
                        </table>
                    </td>
                </tr>
                <tr>
                    <td>
                        <table>
                            <tr>
                                <td><input type="submit" class="btn" value="_("remove selected")"></td>
                            </tr>
                        </table>
                    </td>
                </tr>
                </form>
            </table>
                """)%( slot.getId(),slot.getSession().getColor(), slot.getSession().getColor(),slot.getSession().getTextColor(), slot.getAdjustedStartDate().strftime("%H:%M"),
                        slot.getAdjustedEndDate().strftime("%H:%M"),
                        duration,slot.getSession().getColor(),slot.getSession().getTextColor(),caption,
                        str(addContribURL),
                       str(newContribURL),
                        editSlotLink,delSlotLink,slot.getSession().getTextColor(),convs,slot.getSession().getTextColor(),numEntries,
                        quoteattr(str(delContribsURL)),
                        "".join(entries))

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["day"]=self._day.strftime("%A, %d %B %Y")
        tz = self._session.getTimezone()
        sDate=timezone(tz).localize(datetime(self._day.year,self._day.month,self._day.day,0,0))
        eDate=timezone(tz).localize(datetime(self._day.year,self._day.month,self._day.day,23,59))
        res=[]
        for slotEntry in self._session.getSchedule().getEntries():
            if slotEntry.getAdjustedStartDate()>eDate:
                break
            if slotEntry.getAdjustedEndDate()>=sDate and \
                                slotEntry.getAdjustedStartDate()<=eDate:
                res.append(self._getSlotHTML(slotEntry.getOwner()))
        vars["slots"]="<br>".join(res)
        urlNewSlot=urlHandlers.UHSessionModSlotNew.getURL(self._session)
        urlNewSlot.addParam("slotDate",self._day.strftime("%d-%m-%Y"))
        vars["newSlotURL"]=quoteattr(str(urlNewSlot))
        vars["newSlotBtn"]=""
        if self._session.canModify(self._aw) or self._session.canCoordinate(self._aw, "unrestrictedSessionTT"):
            vars["newSlotBtn"]= _("""<input type="submit" class="btn" value="_("new slot")">""")
        return vars


class WPSessionModifSchedule( WPSessionModifBase, WPConfModifScheduleGraphic  ):

    def __init__( self, rh, session):
        WPSessionModifBase.__init__(self, rh, session)
        WPConfModifScheduleGraphic.__init__( self, rh, session.getConference() )
        self._session = session

    def _setActiveTab(self):
        self._tabTimetable.setActive()

    def getJSFiles(self):
        return WPConfModifScheduleGraphic.getJSFiles(self)

    def _includeFavList(self):
        return True

    def _generateTimetable(self):

        tz = self._conf.getTimezone()
        timeTable = timetable.TimeTable(self._session.getSchedule(), tz)
        sDate,eDate=self._session.getAdjustedStartDate(tz),self._session.getAdjustedEndDate(tz)
        timeTable.setStartDate(sDate)
        timeTable.setEndDate(eDate)
#        timeTable.setStartDayTime(7,0)
#        timeTable.setEndDayTime(21,59)

        timeTable.mapEntryList(self._session.getSchedule().getEntries())
        return timeTable

    def _getSchedule(self):
        return WSessionModifSchedule(self._session, self._timetable, self._days)

    def _getTabContent( self, params ):
        return self._getTTPage(params)

class WSessionModifSchedule(wcomponents.WTemplated):

    def __init__(self, session, timetable, dayList, **params):
        wcomponents.WTemplated.__init__(self, **params)
        self._session = session
        self._timetable = timetable
        self._dayList = dayList

    def getVars( self ):
        vars=wcomponents.WTemplated.getVars(self)
        tz = self._session.getTimezone()
        vars["timezone"]= tz
        # the list of days specified by the user through the option box
        vars["daysParam"] = self._dayList
        # the list of days from the timetable
        vars["dayList"]=self._timetable.getDayList()
        # the first day of the list
        vars["dayDate"]=self._dayList[0].getDate()

        vars['rbActive'] = info.HelperMaKaCInfo.getMaKaCInfoInstance().getRoomBookingModuleActive()

        vars['ttdata'] = simplejson.dumps(schedule.ScheduleToJson.process(self._session.getSchedule(), tz, None))

        eventInfo = DictPickler.pickle(self._session.getConference(), timezone=tz)
        eventInfo['timetableSession'] = DictPickler.pickle(self._session, timezone=tz)
        vars['eventInfo'] = simplejson.dumps(eventInfo)

        return vars

class ContainerIndexItem:

    def __init__(self, container, day):
        self._overlap = container.getMaxOverlap(day)
        self._startPosition = -1
        self._entryList = []
        for i in range(0,self._overlap):
            self._entryList.append(None)

    def setStartPosition(self, counter):
        self._startPosition = counter

    def getStartPosition(self):
        return self._startPosition

    def setEntryList(self, newEntryList):
        # -- Remove the ones which are not in the new entry list
        i = 0
        for entry in self._entryList:
            if entry not in newEntryList:
                self._entryList[i] = None
            i += 1
        # -- Add the new ones to the new entry list
        for newEntry in newEntryList:
            if newEntry not in self._entryList:
                i = 0
                for entry in self._entryList:
                    if entry == None:
                        self._entryList[i] = newEntry
                        break
                    i += 1

    def getEntryIndex(self, i):
        return self._startPosition + i

    def getEntryByPosition(self, i):
        if i >= 0 and i < len(self._entryList):
            return self._entryList[i]
        return 0

    def getOverlap(self):
        return self._overlap

class ContainerIndex:

    def __init__(self, containerIndex = {}, day = None, hasOverlap = False):
        self._containerIndex = containerIndex
        self._day = day
        self._rowsCounter = 0
        self._hasOverlap = hasOverlap

    def initialization(self, day, hasOverlap = False):
        self._containerIndex={}
        self._day = day
        self._rowsCounter = 0
        self._hasOverlap = hasOverlap

    def hasOverlap(self):
        return self._hasOverlap

    def setHasOverlap(self, hasOverlap):
        self._hasOverlap = hasOverlap

    def addContainer(self, container):
        if not self._containerIndex.has_key(container):
            item = ContainerIndexItem(container, self._day)
            item.setStartPosition(self._rowsCounter)
            if self.hasOverlap():
                self._rowsCounter += item.getOverlap()
            self._containerIndex[container] = item

    def setContainerEntries(self, container, entryList):
        if self._containerIndex.has_key(container):
            self._containerIndex[container].setEntryList(entryList)

    def getEntryIndex(self, container, i):
        if self._containerIndex.has_key(container):
            contItem = self._containerIndex[container]
            return contItem.getEntryIndex(i)
        return 0

    def getEntryByPosition(self, container, i):
        if self._containerIndex.has_key(container):
            contItem = self._containerIndex[container]
            return contItem.getEntryByPosition(i)
        return 0

    def getMaxOverlap(self, container):
        if self._containerIndex.has_key(container):
            contItem = self._containerIndex[container]
            return contItem.getOverlap()
        return 0

    def getStartPosition(self, container):
        if self._containerIndex.has_key(container):
            contItem = self._containerIndex[container]
            return contItem.getStartPosition()
        return 0


class WPSessionModifyBreak( WPSessionModifSchedule ):

    def __init__(self,rh,conf,schBreak):
        WPSessionModifSchedule.__init__(self,rh,conf)
        self._break=schBreak

    def _getScheduleContent(self,params):
        sch=self._conf.getSchedule()
        wc=wcomponents.WBreakDataModification(sch,self._break,conf=self._conf)
        pars = { "postURL": urlHandlers.UHSessionPerformModifyBreak.getURL(self._break) }
        params["body"] = wc.getHTML( pars )
        return wcomponents.WBreakModifHeader( self._break, self._getAW() ).getHTML( params )



class WPModSchEditContrib(WPSessionModifSchedule):

    def __init__(self,rh,contrib):
        WPSessionModifSchedule.__init__(self,rh,contrib.getSession())
        self._contrib=contrib

    def _getTabContent(self,params):
        if self._contrib.getSession().getScheduleType() == "poster":
            wc=WSessionModContribListEditContrib(self._contrib)
        else:
            wc=wcomponents.WSchEditContrib(self._contrib)
        pars={"postURL":urlHandlers.UHSessionModSchEditContrib.getURL(self._contrib)}
        return wc.getHTML(pars)

class WSessionAddSlot(wcomponents.WTemplated):

    def __init__(self, slotData , conf, errors=[]):
        self._session = slotData.getSession()
        self._slotData = slotData
        self._errors=errors
        self._conf = conf

    def _getConvenersHTML(self):
        res=[]
        for conv in self._slotData.getConvenerList():
            tmp= _("""
                    <tr>
                        <td style="border-top:1px solid #777777;border-left:1px solid #777777;" width="100%%">
                            <input type="checkbox" name="sel_conv" value=%s>
                            <input type="hidden" name="conv_id" value=%s>
                        </td>
                        <td style="border-top:1px solid #777777;padding-top:2px" width="100%%">
                            <table border="0" width="95%%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td>&nbsp;</td>
                                </tr>
                                <tr>
                                    <td nowrap>
                                         _("Title") <select name="conv_title">%s</select>
                                    </td>
                                </tr>
                                <tr>
                                    <td nowrap>
                                         _("Family name") <input type="text" size="40" name="conv_family_name" value=%s>
                                         _("First name") <input type="text" size="30" name="conv_first_name" value=%s>
                                    </td>
                                </tr>
                                <tr>
                                    <td nowrap>
                                         _("Affiliation") <input type="text" size="40" name="conv_affiliation" value=%s>
                                        _("Email") <input type="text" size="39" name="conv_email" value=%s>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr><td colspan="3">&nbsp;</td></tr>
                """)%(quoteattr(str(conv.getId())),\
                    quoteattr(str(conv.getId())),\
                    TitlesRegistry.getSelectItemsHTML(conv.getTitle()), \
                    quoteattr(conv.getFamilyName()),\
                    quoteattr(conv.getFirstName()), \
                    quoteattr(conv.getAffiliation()), \
                    quoteattr(conv.getEmail()) )
            res.append(tmp)
        return "".join(res)

    def _getErrorHTML( self, msgList ):
        if not msgList:
            return ""
        return """
            <table align="center" cellspacing="0" cellpadding="0">
                <tr>
                    <td>
                        <table align="center" valign="middle" style="padding:10px; border:1px solid #5294CC; background:#F6F6F6">
                            <tr><td>&nbsp;</td><td>&nbsp;</td></tr>
                            <tr>
                                <td>&nbsp;</td>
                                <td><font color="red">%s</font></td>
                                <td>&nbsp;</td>
                            </tr>
                            <tr><td>&nbsp;</td><td>&nbsp;</td></tr>
                        </table>
                    </td>
                </tr>
            </table>
                """%"<br>".join( msgList )


    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["calendarIconURL"]=Config.getInstance().getSystemIconURL( "calendar" )
        vars["calendarSelectURL"]=urlHandlers.UHSimpleCalendar.getURL()
        defaultDefinePlace = defaultDefineRoom = ""
        defaultInheritPlace = defaultInheritRoom = "checked"
        locationName, locationAddress, roomName,defaultExistRoom = "", "", "",""
        slotSd = self._slotData.getStartDate()
        slotEd = self._slotData.getEndDate()
        vars["title"]=self._slotData.getTitle()
        vars["sDay"] = slotSd.day
        vars["sMonth"] = slotSd.month
        vars["sYear"] = slotSd.year
        vars["sHour"] = slotSd.hour
        vars["sMinute"] = slotSd.minute
        vars["eDay"] = slotEd.day
        vars["eMonth"] = slotEd.month
        vars["eYear"] = slotEd.year
        vars["eHour"] = slotEd.hour
        vars["eMinute"] = slotEd.minute
        vars["contribDurHours"] = ""
        vars["contribDurMins"] = ""
        if self._slotData.getContribDuration() != None:
            vars["contribDurHours"] = (datetime(1900,1,1)+self._slotData.getContribDuration()).hour
            vars["contribDurMins"] = (datetime(1900,1,1)+self._slotData.getContribDuration()).minute
        if self._slotData.getLocationName() !="":
            defaultDefinePlace = "checked"
            defaultInheritPlace = ""
            locationName = self._slotData.getLocationName()
            locationAddress = self._slotData.getLocationAddress()
        if self._slotData.getRoomName() != "":
            defaultDefineRoom= "checked"
            defaultInheritRoom = ""
            defaultExistRoom = ""
            roomName = self._slotData.getRoomName()
        vars["defaultInheritPlace"] = defaultInheritPlace
        vars["defaultDefinePlace"] = defaultDefinePlace
        vars["sesPlace"] = ""
        sesLocation = self._slotData.getSession().getLocation()
        if sesLocation:
            vars["sesPlace"] = sesLocation.getName()
        vars["locationName"] = locationName
        vars["locationAddress"] = locationAddress
        vars["defaultInheritRoom"] = defaultInheritRoom
        vars["defaultDefineRoom"] = defaultDefineRoom
        vars["defaultExistRoom"]= defaultExistRoom
        vars["sesRoom"] = ""
        sesRoom = self._slotData.getSession().getRoom()
        if sesRoom:
            vars["sesRoom"] = sesRoom.getName()
        vars["roomName"] = roomName
        vars["conveners"]=self._getConvenersHTML()
        vars["postURL"]=quoteattr(str(urlHandlers.UHSessionModSlotNew.getURL(self._session)))
        vars["errors"]=self._getErrorHTML(self._errors)
        rx=[]
        roomsexist = self._conf.getRoomList()
        roomsexist.sort()
        for room in roomsexist:
            sel=""
            rx.append("""<option value=%s%s>%s</option>"""%(quoteattr(str(room)),
                        sel,self.htmlText(room)))
        vars ["roomsexist"] = "".join(rx)
        vars["autoUpdate"]=""
        return vars


class WPModSlotNew(WPSessionModifSchedule):

    def __init__(self, rh, slotData, errors=[] ):
        WPSessionModifSchedule.__init__(self, rh, slotData.getSession())
        self._slotData = slotData
        self._errors=errors


    def _getTabContent( self, params ):
        wc=WSessionAddSlot(self._slotData, self._conf, self._errors)
        return wc.getHTML()

class WSlotModifMainData(wcomponents.WTemplated):

    def __init__(self, slot, conf, errors=[]):
        self._slotData = slot
        self._errors=errors
        self._conf = conf

    def _getConvenersHTML(self):
        res=[]
        for conv in self._slotData.getConvenerList():
            tmp= _("""
                    <tr>
                        <td style="border-top:1px solid #777777;border-left:1px solid #777777;" width="100%%">
                            <input type="checkbox" name="sel_conv" value=%s>
                            <input type="hidden" name="conv_id" value=%s>
                        </td>
                        <td style="border-top:1px solid #777777;padding-top:2px" width="100%%">
                            <table border="0" width="95%%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td>&nbsp;</td>
                                </tr>
                                <tr>
                                    <td nowrap>
                                         _("Title") <select name="conv_title">%s</select>
                                    </td>
                                </tr>
                                <tr>
                                    <td nowrap>
                                         _("Family name") <input type="text" size="40" name="conv_family_name" value=%s>
                                         _("First name") <input type="text" size="30" name="conv_first_name" value=%s>
                                    </td>
                                </tr>
                                <tr>
                                    <td nowrap>
                                         _("Affiliation") <input type="text" size="40" name="conv_affiliation" value=%s>
                                         _("Email") <input type="text" size="39" name="conv_email" value=%s>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    <tr><td colspan="3">&nbsp;</td></tr>
                """)%(quoteattr(str(conv.getId())),\
                    quoteattr(str(conv.getId())),\
                    TitlesRegistry.getSelectItemsHTML(conv.getTitle()), \
                    quoteattr(conv.getFamilyName()),\
                    quoteattr(conv.getFirstName()), \
                    quoteattr(conv.getAffiliation()), \
                    quoteattr(conv.getEmail()) )
            res.append(tmp)
        return "".join(res)

    def _getErrorHTML( self, msgList ):
        if not msgList:
            return ""
        return """
            <table align="center" cellspacing="0" cellpadding="0">
                <tr>
                    <td>
                        <table align="center" valign="middle" style="padding:10px; border:1px solid #5294CC; background:#F6F6F6">
                            <tr><td>&nbsp;</td><td>&nbsp;</td></tr>
                            <tr>
                                <td>&nbsp;</td>
                                <td><font color="red">%s</font></td>
                                <td>&nbsp;</td>
                            </tr>
                            <tr><td>&nbsp;</td><td>&nbsp;</td></tr>
                        </table>
                    </td>
                </tr>
            </table>
                """%"<br>".join( msgList )

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["calendarIconURL"]=Config.getInstance().getSystemIconURL( "calendar" )
        vars["calendarSelectURL"]=urlHandlers.UHSimpleCalendar.getURL()
        defaultDefinePlace = defaultDefineRoom = ""
        defaultInheritPlace = defaultInheritRoom = "checked"
        locationName, locationAddress, roomName, defaultExistRoom = "", "", "",""
        vars["conference"] = self._conf
        vars["session"] = self._slotData.getSession()
        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        vars["useRoomBookingModule"] = minfo.getRoomBookingModuleActive()
        vars["title"]=self._slotData.getTitle()
        sd = self._slotData.getAdjustedStartDate()
        ed = self._slotData.getAdjustedEndDate()
        vars["sDay"] = sd.day
        vars["sMonth"] = sd.month
        vars["sYear"] = sd.year
        vars["sHour"] = sd.hour
        vars["sMinute"] = sd.minute
        vars["eDay"] = ed.day
        vars["eMonth"] = ed.month
        vars["eYear"] = ed.year
        vars["eHour"] = ed.hour
        vars["eMinute"] = ed.minute
        vars["contribDurHours"] = ""
        vars["contribDurMins"] = ""
        if self._slotData.getContribDuration() != None:
            vars["contribDurHours"] = (datetime(1900,1,1)+self._slotData.getContribDuration()).hour
            vars["contribDurMins"] = (datetime(1900,1,1)+self._slotData.getContribDuration()).minute
        if self._slotData.getLocationName() !="":
            defaultDefinePlace = "checked"
            defaultInheritPlace = ""
            locationName = self._slotData.getLocationName()
            locationAddress = self._slotData.getLocationAddress()
        if self._slotData.getRoomName() != "":
            defaultDefineRoom= "checked"
            defaultInheritRoom = ""
            defaultExistRoom = ""
            roomName = self._slotData.getRoomName()
        vars["defaultInheritPlace"] = defaultInheritPlace
        vars["defaultDefinePlace"] = defaultDefinePlace
        vars["sesPlace"] = ""
        sesLocation = self._slotData.getSession().getLocation()
        if sesLocation:
            vars["sesPlace"] = sesLocation.getName()
        vars["locationName"] = locationName
        vars["locationAddress"] = locationAddress
        vars["defaultInheritRoom"] = defaultInheritRoom
        vars["defaultDefineRoom"] = defaultDefineRoom
        vars["defaultExistRoom"] = defaultExistRoom
        vars["sesRoom"] = ""
        sesRoom = self._slotData.getSession().getRoom()
        if sesRoom:
            vars["sesRoom"] = sesRoom.getName()
        vars["roomName"] = roomName
        rx=[]
        roomsexist = self._conf.getRoomList()
        roomsexist.sort()
        for room in roomsexist:
            rx.append("""<option value=%s>%s</option>"""%(quoteattr(str(room)),
                        self.htmlText(room)))
        vars ["roomsexist"] = "".join(rx)
        vars["conveners"]=self._getConvenersHTML()
        vars["errors"]=self._getErrorHTML(self._errors)
        vars["locator"] = ""
        slot = self._slotData.getSession().getSlotById(self._slotData.getId())
        vars["locator"] = slot.getLocator().getWebForm()
        vars["postURL"]=quoteattr(str(urlHandlers.UHSessionModSlotEdit.getURL(slot)))
        vars["autoUpdate"]=""
        return vars


class WPModSlotEdit(WPConferenceModifBase):

    def __init__(self,rh, slot, errors=[]):
        WPConferenceModifBase.__init__(self,rh,slot.getSession().getConference())
        self._slotData=slot
        self._errors=errors

    def _setActiveSideMenuItem(self):
        self._timetableMenuItem.setActive()

    def _getPageContent( self, params ):
        wc=WSlotModifMainData(self._slotData,self._conf,self._errors)
        return wc.getHTML()

class WSchModifRecalculate(wcomponents.WTemplated):

    def __init__(self, entry):
        self._entry = entry

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["entryType"]="slot"
        vars["title"]=""
        if self._entry.getTitle().strip() != "":
            vars["title"]= _("""
                            <tr>
                                <td nowrap class="titleCellTD"><span class="titleCellFormat"> _("Title")</span></td>
                                <td bgcolor="white" width="100%%">&nbsp;%s</td>
                            </tr>
                            """)%self._entry.getTitle()
        return vars

class WPModSlotCalc(WPConferenceModifBase):

    def __init__(self,rh, slot):
        WPConferenceModifBase.__init__(self,rh,slot.getSession().getConference())
        self._slot=slot

    def _setActiveSideMenuItem(self):
        self._timetableMenuItem.setActive()

    def _getPageContent( self, params ):
        wc=WSchModifRecalculate(self._slot)
        p={"postURL":quoteattr(str(urlHandlers.UHSessionModSlotCalc.getURL(self._slot)))}
        return wc.getHTML(p)

class WPModSlotRemConfirmation(WPSessionModifSchedule):

    def __init__(self,rh,slot):
        WPSessionModifSchedule.__init__(self,rh,slot.getSession())
        self._slot=slot

    def _getTabContent(self,params):
        wc=wcomponents.WConfirmation()
        slotCaption="on %s %s-%s"%(
            self._slot.getAdjustedStartDate().strftime("%A %d %B %Y"),
            self._slot.getAdjustedStartDate().strftime("%H:%M"),
            self._slot.getAdjustedEndDate().strftime("%H:%M"))
        if self._slot.getTitle()!="":
            slotCaption=""" "%s" (%s) """%(self._slot.getTitle(),slotCaption)

        msg= _("""Are you sure you want to delete the slot %s
        (note that any contribution scheduled
        inside will be unscheduled)?""")%(slotCaption)
        url=urlHandlers.UHSessionModSlotRem.getURL(self._slot)
        return wc.getHTML(msg,url,{})


class WPModScheduleAddContrib(WPSessionModifSchedule):

    def _getTabContent( self, params ):
        target=self._session
        if params.get("slot",None) is not None:
            target=params["slot"]
        l=[]
        for contrib in self._session.getContributionList():
            if contrib.isScheduled() or isinstance(contrib.getCurrentStatus(),conference.ContribStatusWithdrawn):
                continue
            l.append(contrib)
        p=wcomponents.WScheduleAddContributions(l)
        pars={"postURL":urlHandlers.UHSessionModScheduleAddContrib.getURL(target)}
        return p.getHTML(pars)

class WPModScheduleNewContrib(WPModScheduleNewContribBase, WPSessionModifSchedule):

    def __init__(self, rh, ses, targetDay):
        WPSessionModifSchedule.__init__(self, rh, ses)
        WPModScheduleNewContribBase.__init__(self, targetDay)

class WSessionModifSchContribCreation(WContributionCreation):

    def __init__(self, slot):
        WContributionCreation.__init__(self, slot.getConference())
        self._slot = slot

    def getVars(self):
        vars=WContributionCreation.getVars(self)
        if self._slot is not None:
            d=self._slot.getSchedule().calculateDayEndDate(self._slot.getAdjustedStartDate())
            vars["day"]=d.day
            vars["month"]=d.month
            vars["year"]=d.year
            vars["sHour"]=d.hour
            vars["sMinute"]=d.minute
            vars["durationHours"],vars["durationMinutes"]="0","20"
            vars["poster"]=""
            if self._slot.getSession().getScheduleType() == "poster":
                vars["poster"]="disabled"
        return vars


class WPSessionAddBreak(WPSessionModifSchedule):

    def __init__(self,rh,slot):
        WPSessionModifSchedule.__init__(self,rh,slot.getSession())
        self._slot=slot

    def _getTabContent( self, params ):
        s = self._slot.getSchedule()
        day = self._slot.getAdjustedStartDate()
        p=wcomponents.WBreakDataModification(self._slot.getSchedule(),conf=self._slot.getConference(),targetDay=day)
        pars = {"postURL":urlHandlers.UHSessionAddBreak.getURL(self._slot)}
        return p.getHTML(pars)



class WSessionModifAC(wcomponents.WTemplated):

    def __init__(self,session):
        self._session=session

    def _getCoordinatorsHTML(self):
        res = wcomponents.WPrincipalTable().getHTML( list(self._session.getCoordinatorList()), self._session, str(urlHandlers.UHSessionModCoordinatorsSel.getURL()), str(urlHandlers.UHSessionModCoordinatorsRem.getURL()), pendings=self._session.getCoordinatorEmailList(), selectable=False )
        return res

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        wc=wcomponents.WAccessControlFrame()
        vars["accessControlFrame"]=wc.getHTML(self._session,\
                                urlHandlers.UHSessionSetVisibility.getURL(),\
                                urlHandlers.UHSessionSelectAllowed.getURL(),\
                                urlHandlers.UHSessionRemoveAllowed.getURL())
        if not self._session.isProtected():
            df=wcomponents.WDomainControlFrame(self._session)
            vars["accessControlFrame"] += "<br>%s"%df.getHTML( \
                                    urlHandlers.UHSessionAddDomains.getURL(),\
                                    urlHandlers.UHSessionRemoveDomains.getURL())
        wc=wcomponents.WModificationControlFrame()
        vars["modifyControlFrame"]=wc.getHTML(self._session,\
                                urlHandlers.UHSessionSelectManagers.getURL(),\
                                urlHandlers.UHSessionRemoveManagers.getURL() )
        vars["coordinators"]=self._getCoordinatorsHTML()
        return vars


class WPSessionModifAC( WPSessionModifBase ):

    def _setActiveTab( self ):
        self._tabAC.setActive()

    def _getTabContent( self, params ):
        comp=WSessionModifAC(self._session)
        return comp.getHTML()


class WPSessionSelectAllowed( WPSessionModifAC ):

    def _getTabContent( self, params ):
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        wc = wcomponents.WPrincipalSelection( urlHandlers.UHSessionSelectAllowed.getURL(),forceWithoutExtAuth=searchLocal )
        params["addURL"] = urlHandlers.UHSessionAddAllowed.getURL()
        return wc.getHTML( params )


class WPSessionSelectManagers( WPSessionModifAC ):

    def _getTabContent( self, params ):
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        wc = wcomponents.WPrincipalSelection( urlHandlers.UHSessionSelectManagers.getURL(), addTo=3,forceWithoutExtAuth=searchLocal)
        params["addURL"] = urlHandlers.UHSessionAddManagers.getURL()
        return wc.getHTML( params )


class WPModCoordinatorsSel(WPSessionModifAC):

    def _getTabContent(self,params):
        searchExt = params.get("searchExt","")
        if searchExt != "":
            searchLocal = False
        else:
            searchLocal = True
        url=urlHandlers.UHSessionModCoordinatorsSel.getURL()
        wc =wcomponents.WPrincipalSelection(url, addTo=3,forceWithoutExtAuth=searchLocal)
        wc.setTitle( _("Selecting session coordinators") )
        params["addURL"]=urlHandlers.UHSessionModCoordinatorsAdd.getURL()
        return wc.getHTML( params )


class WSessionModifTools(wcomponents.WTemplated):

    def __init__( self, session ):
        self.__session = session

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["deleteIconURL"] = Config.getInstance().getSystemIconURL("delete")
        vars["writeIconURL"] = Config.getInstance().getSystemIconURL("write_minutes")
        vars["closeIconURL"] = Config.getInstance().getSystemIconURL("closeIcon")
        vars["closeURL"] = urlHandlers.UHSessionClose.getURL(self.__session)
        return vars


class WPSessionModifComm( WPSessionModifBase ):

    def _setActiveTab( self ):
        self._tabComm.setActive()

    def _getTabContent( self, params ):
        wc = wcomponents.WSessionModifComm( self._getAW(),self._session )
        pars = {
                "editCommentsURLGen":urlHandlers.UHSessionModifCommEdit.getURL
               }
        return wc.getHTML( pars )


class WPSessionCommEdit( WPSessionModifBase ):

    def _setActiveTab( self ):
        self._tabComm.setActive()

    def _getTabContent(self,params):
        self._comment = self._session.getComments()
        wc = wcomponents.WSessionModifCommEdit(self._comment)
        p={"postURL":urlHandlers.UHSessionModifCommEdit.getURL(self._session)}
        return wc.getHTML(p)



class WPSessionModifTools( WPSessionModifBase ):

    def _setActiveTab( self ):
        self._tabTools.setActive()

    def _getTabContent( self, params ):
        comp = WSessionModifTools( self._session )
        pars = {
"deleteSessionURL": urlHandlers.UHSessionDeletion.getURL( self._session ), \
"writeMinutesURL": urlHandlers.UHSessionWriteMinutes.getURL( self._session ) \
               }
        return comp.getHTML( pars )


class WPSessionDeletion( WPSessionModifTools ):

    def _getTabContent( self, params ):
        msg = _("""
        <font size="+2">_("Are you sure that you want to DELETE the session '%s'")?</font><br>(_("Note that if you delete the
session, all the items below it will also be deleted"))
              """)%(self._session.getTitle())
        wc = wcomponents.WConfirmation()
        return wc.getHTML( msg, \
                        urlHandlers.UHSessionDeletion.getURL( self._session ), \
                        {}, \
                        confirmButtonCaption= _("Yes"), cancelButtonCaption= _("No") )


class WPSessionWriteMinutes( WPSessionModifTools ):

    def _getTabContent( self, params ):
        wc = wcomponents.WWriteMinutes( self._session )
        pars = {"postURL": urlHandlers.UHSessionWriteMinutes.getURL(self._session) }
        return wc.getHTML( pars )


class WSessionModContribList(wcomponents.WTemplated):

    def __init__(self,session,filter,sorting,order, aw):
        self._session=session
        self._conf=self._session.getConference()
        self._filterCrit=filter
        self._sortingCrit=sorting
        self._order = order
        self._totaldur =timedelta(0)
        self._aw=aw

    def _getURL( self ):
        #builds the URL to the contribution list page
        #   preserving the current filter and sorting status
        url = urlHandlers.UHSessionModContribList.getURL(self._session)
        if self._filterCrit.getField("type"):
            l=[]
            for t in self._filterCrit.getField("type").getValues():
                if t!="":
                    l.append(t)
            url.addParam("types",l)
            if self._filterCrit.getField("type").getShowNoValue():
                url.addParam("typeShowNoValue","1")

        if self._filterCrit.getField("track"):
            url.addParam("tracks",self._filterCrit.getField("track").getValues())
            if self._filterCrit.getField("track").getShowNoValue():
                url.addParam("trackShowNoValue","1")

        if self._filterCrit.getField("status"):
            url.addParam("status",self._filterCrit.getField("status").getValues())

        if self._filterCrit.getField("material"):
            url.addParam("material",self._filterCrit.getField("material").getValues())

        if self._sortingCrit.getField():
            url.addParam("sortBy",self._sortingCrit.getField().getId())
            url.addParam("order","down")
        url.addParam("OK","1")
        return url

    def _getMaterialsHTML(self, contrib, matUrlHandler):
        materials=[]
        if contrib.getPaper() is not None:
            url=matUrlHandler.getURL(contrib.getPaper())
            iconHTML="""<img border="0" src=%s alt="paper">"""%quoteattr(str(materialFactories.PaperFactory.getIconURL()))
            if len(contrib.getPaper().getResourceList())>0:
                r=contrib.getPaper().getResourceList()[0]
                if isinstance(r,conference.Link):
                    iconHTML="""<a href=%s>%s</a>"""%(quoteattr(str(r.getURL())),iconHTML)
                elif isinstance(r,conference.LocalFile):
                    iconHTML="""<a href=%s>%s</a>"""%(quoteattr(str(urlHandlers.UHFileAccess.getURL(r))),iconHTML)
            materials.append("""%s<a href=%s>%s</a>"""%(iconHTML,quoteattr(str(url)),self.htmlText(materialFactories.PaperFactory.getTitle().lower())))
        if contrib.getSlides() is not None:
            url=matUrlHandler.getURL(contrib.getSlides())
            iconHTML="""<img border="0" src=%s alt="slides">"""%quoteattr(str(materialFactories.SlidesFactory.getIconURL()))
            if len(contrib.getSlides().getResourceList())>0:
                r=contrib.getSlides().getResourceList()[0]
                if isinstance(r,conference.Link):
                    iconHTML="""<a href=%s>%s</a>"""%(quoteattr(str(r.getURL())),iconHTML)
                elif isinstance(r,conference.LocalFile):
                    iconHTML="""<a href=%s>%s</a>"""%(quoteattr(str(urlHandlers.UHFileAccess.getURL(r))),iconHTML)
            materials.append("""%s<a href=%s>%s</a>"""%(iconHTML,quoteattr(str(url)),self.htmlText(materialFactories.SlidesFactory.getTitle().lower())))
        if contrib.getPoster() is not None:
            url=matUrlHandler.getURL(contrib.getPoster())
            iconHTML="""<img border="0" src=%s alt="slides">"""%quoteattr(str(materialFactories.PosterFactory.getIconURL()))
            if len(contrib.getPoster().getResourceList())>0:
                r=contrib.getPoster().getResourceList()[0]
                if isinstance(r,conference.Link):
                    iconHTML="""<a href=%s>%s</a>"""%(quoteattr(str(r.getURL())),iconHTML)
                elif isinstance(r,conference.LocalFile):
                    iconHTML="""<a href=%s>%s</a>"""%(quoteattr(str(urlHandlers.UHFileAccess.getURL(r))),iconHTML)
            materials.append("""%s<a href=%s>%s</a>"""%(iconHTML,quoteattr(str(url)),self.htmlText(materialFactories.PosterFactory.getTitle().lower())))
        video=contrib.getVideo()
        if video is not None:
            materials.append("""<a href=%s><img src=%s border="0" alt="video"> %s</a>"""%(
                quoteattr(str(matUrlHandler.getURL(video))),
                quoteattr(str(materialFactories.VideoFactory.getIconURL())),
                self.htmlText(materialFactories.VideoFactory.getTitle())))
        minutes=contrib.getMinutes()
        if minutes is not None:
            materials.append("""<a href=%s><img src=%s border="0" alt="minutes"> %s</a>"""%(
                quoteattr(str(matUrlHandler.getURL(minutes))),
                quoteattr(str(materialFactories.MinutesFactory.getIconURL())),
                self.htmlText(materialFactories.MinutesFactory.getTitle())))
        iconURL=quoteattr(str(Config.getInstance().getSystemIconURL("material")))
        for material in contrib.getMaterialList():
            url=matUrlHandler.getURL(material)
            materials.append("""<a href=%s><img src=%s border="0" alt=""> %s</a>"""%(
                quoteattr(str(url)),iconURL,self.htmlText(material.getTitle())))
        return "<br>".join(materials)

    def _getContribHTML(self,contrib):
        sdate = ""
        if contrib.getAdjustedStartDate() is not None:
            sdate=contrib.getAdjustedStartDate().strftime("%Y-%b-%d %H:%M" )
        title = """<a href=%s>%s</a>"""%( quoteattr( str( urlHandlers.UHContributionModification.getURL( contrib ) ) ), self.htmlText( contrib.getTitle() ))
        strdur = ""
        if contrib.getDuration() is not None and contrib.getDuration().seconds != 0:
            strdur = (datetime(1900,1,1)+ contrib.getDuration()).strftime("%Hh%M'")
            dur = contrib.getDuration()
            self._totaldur = self._totaldur + dur
        l = []
        for spk in contrib.getSpeakerList():
            l.append( self.htmlText( spk.getFullName() ) )
        speaker = "<br>".join( l )
        track = ""
        if contrib.getTrack():
            track = self.htmlText( contrib.getTrack().getCode() )
        cType=""
        if contrib.getType() is not None:
            cType=contrib.getType().getName()
        status=ContribStatusList().getCode(contrib.getCurrentStatus().__class__)
        if self._session.canCoordinate(self._aw,"modifContribs") or self._session.canModify(self._aw):
            matUrlHandler=urlHandlers.UHMaterialModification
        else:
            matUrlHandler=urlHandlers.UHMaterialDisplay
        html = """
            <tr>
                <td><input type="checkbox" name="contributions" value=%s></td>
                <td valign="top" class="abstractLeftDataCell" nowrap>%s</td>
                <td valign="top" nowrap class="abstractDataCell">%s</td>
                <td valign="top" class="abstractDataCell">%s</td>
                <td valign="top" class="abstractDataCell">%s</td>
                <td valign="top" class="abstractDataCell">%s</td>
                <td valign="top" class="abstractDataCell">%s</td>
                <td valign="top" class="abstractDataCell">%s</td>
                <td valign="top" class="abstractDataCell">%s</td>
                <td valign="top" class="abstractDataCell">%s</td>
            </tr>
                """%(quoteattr(str(contrib.getId())),\
                    self.htmlText(contrib.getId()),sdate or "&nbsp;",\
                    strdur or "&nbsp;",cType or "&nbsp;",title or "&nbsp;", speaker or "&nbsp;",\
                    track or "&nbsp;",status or "&nbsp;", self._getMaterialsHTML(contrib,matUrlHandler) or "&nbsp;")
        return html

    def _getTypeItemsHTML(self):
        checked=""
        if self._filterCrit.getField("type").getShowNoValue():
            checked=" checked"
        res=[ _("""<input type="checkbox" name="typeShowNoValue" value="--none--"%s>--_("not specified")--""")%checked]
        for t in self._conf.getContribTypeList():
            checked=""
            if t.getId() in self._filterCrit.getField("type").getValues():
                checked=" checked"
            res.append("""<input type="checkbox" name="types" value=%s%s> %s"""%(quoteattr(str(t.getId())),checked,self.htmlText(t.getName())))
        return "<br>".join(res)

    def _getTrackItemsHTML(self):
        checked=""
        if self._filterCrit.getField("track").getShowNoValue():
            checked=" checked"
        res=[ _("""<input type="checkbox" name="trackShowNoValue" value="--none--"%s>--_("not specified")--""")%checked]
        for t in self._conf.getTrackList():
            checked=""
            if t.getId() in self._filterCrit.getField("track").getValues():
                checked=" checked"
            res.append("""<input type="checkbox" name="tracks" value=%s%s> (%s) %s"""%(quoteattr(str(t.getId())),checked,self.htmlText(t.getCode()),self.htmlText(t.getTitle())))
        return "<br>".join(res)

    def _getStatusItemsHTML(self):
        res=[]
        for st in ContribStatusList().getList():
            id=ContribStatusList().getId(st)
            checked=""
            if id in self._filterCrit.getField("status").getValues():
                checked=" checked"
            code=ContribStatusList().getCode(st)
            caption=ContribStatusList().getCaption(st)
            res.append("""<input type="checkbox" name="status" value=%s%s> (%s) %s"""%(quoteattr(str(id)),checked,self.htmlText(code),self.htmlText(caption)))
        return "<br>".join(res)

    def _getMaterialItemsHTML(self):
        res=[]
        pf,sf=materialFactories.PaperFactory(),materialFactories.SlidesFactory()
        for (id,caption) in [(pf.getId(),pf.getTitle()),\
                        (sf.getId(),sf.getTitle()),\
                        ("--other--", _("other")),("--none--", _("""--_("no material")--"""))]:
            checked=""
            if id in self._filterCrit.getField("material").getValues():
                checked=" checked"
            res.append("""<input type="checkbox" name="material" value=%s%s> %s"""%(quoteattr(str(id)),checked,self.htmlText(caption)))
        return "<br>".join(res)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["quickAccessURL"]=quoteattr(str(urlHandlers.UHSessionModContribQuickAccess.getURL(self._session)))
        vars["filterPostURL"]=quoteattr(str(urlHandlers.UHSessionModContribList.getURL(self._session)))
        vars["types"]=self._getTypeItemsHTML()
        vars["tracks"]=self._getTrackItemsHTML()
        vars["status"]=self._getStatusItemsHTML()
        vars["materials"]=self._getMaterialItemsHTML()
        vars["authSearch"]=""
        authField=self._filterCrit.getField("author")
        if authField is not None:
            vars["authSearch"]=quoteattr(str(authField.getValues()))
        sortingField = self._sortingCrit.getField()
        self._currentSorting=""
        if sortingField is not None:
            self._currentSorting=sortingField.getId()
        vars["currentSorting"]=""
        url=self._getURL()
        url.addParam("sortBy","number")
        vars["numberImg"]=""
        if self._currentSorting == "number":
            vars["currentSorting"] = """<input type="hidden" name="sortBy" value="number">"""
            if self._order == "down":
                vars["numberImg"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["numberImg"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["numberSortingURL"]=quoteattr(str(url))

        url = self._getURL()
        url.addParam("sortBy", "date")
        vars["dateImg"] = ""
        if self._currentSorting == "date":
            vars["currentSorting"]="""<input type="hidden" name="sortBy" value="date">"""
            if self._order == "down":
                vars["dateImg"]="""<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["dateImg"]="""<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["dateSortingURL"]=quoteattr(str(url))

        url = self._getURL()
        url.addParam("sortBy", "board_number")
        vars["boardNumImg"]=""
        if self._currentSorting == "board_number":
            vars["currentSorting"]="""<input type="hidden" name="sortBy" value="board_number">"""
            if self._order == "down":
                vars["boardNumImg"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["boardNumImg"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["boardNumSortingURL"]=quoteattr(str(url))

        url = self._getURL()
        url.addParam("sortBy", "type")
        vars["typeImg"] = ""
        if self._currentSorting == "type":
            vars["currentSorting"]="""<input type="hidden" name="sortBy" value="type">"""
            if self._order == "down":
                vars["typeImg"]="""<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["typeImg"]="""<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["typeSortingURL"] = quoteattr( str( url ) )

        url = self._getURL()
        url.addParam("sortBy", "name")
        vars["titleImg"] = ""
        if self._currentSorting == "name":
            vars["currentSorting"]="""<input type="hidden" name="sortBy" value="name">"""
            if self._order == "down":
                vars["titleImg"]="""<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["titleImg"]="""<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["titleSortingURL"]=quoteattr(str(url))

        url = self._getURL()
        url.addParam("sortBy", "speaker")
        vars["speakerImg"]=""
        if self._currentSorting=="speaker":
            vars["currentSorting"] = """<input type="hidden" name="sortBy" value="speaker">"""
            if self._order == "down":
                vars["speakerImg"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["speakerImg"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["speakerSortingURL"]=quoteattr( str( url ) )

        url = self._getURL()
        url.addParam("sortBy","track")
        vars["trackImg"] = ""
        if self._currentSorting == "track":
            vars["currentSorting"] = """<input type="hidden" name="sortBy" value="track">"""
            if self._order == "down":
                vars["trackImg"] = """<img src=%s alt="down">"""%(quoteattr(Config.getInstance().getSystemIconURL("downArrow")))
                url.addParam("order","up")
            elif self._order == "up":
                vars["trackImg"] = """<img src=%s alt="up">"""%(quoteattr(Config.getInstance().getSystemIconURL("upArrow")))
                url.addParam("order","down")
        vars["trackSortingURL"] = quoteattr( str( url ) )
        l = []
        numContribs=0
        f=filters.SimpleFilter(self._filterCrit,self._sortingCrit)
        contribsToPrint = []
        for contrib in f.apply(self._session.getContributionList()):
            l.append( self._getContribHTML( contrib ) )
            numContribs+=1
            contribsToPrint.append("""<input type="hidden" name="contributions" value="%s">"""%contrib.getId())
        if self._order =="up":
            l.reverse()
        vars["contributions"]="".join(l)
        vars["contribsToPrint"] = "".join(contribsToPrint)
        vars["contributionActionURL"]=quoteattr(str(urlHandlers.UHSessionModContributionAction.getURL(self._session)))
        vars["contributionsPDFURL"]=quoteattr(str(urlHandlers.UHSessionModToPDF.getURL(self._session)))
        vars["participantListURL"]=quoteattr(str(urlHandlers.UHSessionModParticipantList.getURL(self._session)))
        vars["addContribURL"]=quoteattr(str(urlHandlers.UHSessionModAddContribs.getURL(self._session)))
        vars["numContribs"]=str(numContribs)
        totaldur = self._totaldur
        days = totaldur.days
        hours = (totaldur.seconds)/3600
        dayhours = (days * 24)+hours
        mins = ((totaldur.seconds)/60)-(hours*60)
        vars["totaldur" ]="""%sh%sm"""%(dayhours,mins)
        return vars


class WSessionModPosterContribList(WSessionModContribList):

    def _getContribHTML(self,contrib):
        sdate = ""
        if contrib.getAdjustedStartDate() is not None:
            sdate=contrib.getAdjustedStartDate().strftime("%Y-%b-%d %H:%M" )
        strdur = ""
        if contrib.getDuration() is not None and contrib.getDuration().seconds != 0:
            strdur = (datetime(1900,1,1)+ contrib.getDuration()).strftime("%Hh%M'")
            dur = contrib.getDuration()
            self._totaldur = self._totaldur + dur
        title = """<a href=%s>%s</a>"""%( quoteattr( str( urlHandlers.UHContributionModification.getURL( contrib ) ) ), self.htmlText( contrib.getTitle() ))
        l = []
        for spk in contrib.getSpeakerList():
            l.append( self.htmlText( spk.getFullName() ) )
        speaker = "<br>".join( l )
        track = ""
        if contrib.getTrack():
            track = self.htmlText( contrib.getTrack().getCode() )
        cType=""
        if contrib.getType() is not None:
            cType=contrib.getType().getName()
        status=ContribStatusList().getCode(contrib.getCurrentStatus().__class__)
        materials=""
        if contrib.getPaper() is not None:
            url=urlHandlers.UHMaterialModification.getURL(contrib.getPaper())
            materials+="""<a href=%s><img border="0" src=%s alt="paper"></a>"""%(
                    quoteattr(str(url)),
                    quoteattr(str(materialFactories.PaperFactory().getIconURL())))
        if contrib.getSlides() is not None:
            url=urlHandlers.UHMaterialModification.getURL(contrib.getSlides())
            materials+="""<a href=%s><img border="0" src=%s alt="slides"></a>"""%(
                    quoteattr(str(url)),
                    quoteattr(str(materialFactories.SlidesFactory().getIconURL())))
        editURL=urlHandlers.UHSessionModContribListEditContrib.getURL(contrib)
        if self._currentSorting!="":
            editURL.addParam("sortBy",self._currentSorting)
        editIconURL=Config.getInstance().getSystemIconURL("modify")
        html = """
            <tr>
                <td><input type="checkbox" name="contributions" value=%s></td>
                <td valign="top" class="abstractLeftDataCell" nowrap>%s</td>
                <td valign="top" nowrap class="abstractDataCell">%s</td>
                <td valign="top" class="abstractDataCell">%s</td>
                <td valign="top" class="abstractDataCell">%s</td>
                <td valign="top" class="abstractDataCell"><a href=%s><img src=%s border="0" alt=""></a>%s</td>
                <td valign="top" class="abstractDataCell">%s</td>
                <td valign="top" class="abstractDataCell">%s</td>
                <td valign="top" class="abstractDataCell">%s</td>
                <td valign="top" class="abstractDataCell">%s</td>
                <td valign="top" class="abstractDataCell">%s</td>
            </tr>
                """%(quoteattr(str(contrib.getId())),
                    self.htmlText(contrib.getId()),
                    sdate or "&nbsp;",
                    strdur or "&nbsp;",
                    cType or "&nbsp;",
                    quoteattr(str(editURL)),
                    quoteattr(str(editIconURL)),title or "&nbsp;",
                    speaker or "&nbsp;",
                    track or "&nbsp;",
                    status or "&nbsp;",
                    materials or "&nbsp;",
                    self.htmlText(contrib.getBoardNumber()) or "&nbsp;")
        return html


class WPModContribList(WPSessionModifBase):

    def _setActiveTab(self):
        self._tabContribs.setActive()

    def _getTabContent( self, params ):
        filterCrit=params.get("filterCrit",None)
        sortingCrit=params.get("sortingCrit",None)
        order = params.get("order","down")
        if self._session.getScheduleType()=="poster":
            wc=WSessionModPosterContribList(self._session,filterCrit,sortingCrit, order, self._getAW())
        else:
            wc=WSessionModContribList(self._session,filterCrit,sortingCrit, order, self._getAW())
        return wc.getHTML()


class WSessionModContribListEditContrib(wcomponents.WTemplated):

    def __init__(self,contrib):
        self._contrib=contrib

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        url=vars["postURL"]
        if vars.get("sortBy","").strip()!="":
            url.addParam("sortBy",vars["sortBy"])
        vars["postURL"]=quoteattr(str(url))
        vars["title"]=self.htmlText(self._contrib.getTitle())
        defaultDefinePlace=defaultDefineRoom=""
        defaultInheritPlace=defaultInheritRoom="checked"
        locationName,locationAddress,roomName="","",""
        if self._contrib.getOwnLocation():
            defaultDefinePlace,defaultInheritPlace="checked",""
            locationName=self._contrib.getLocation().getName()
            locationAddress=self._contrib.getLocation().getAddress()
        if self._contrib.getOwnRoom():
            defaultDefineRoom,defaultInheritRoom="checked",""
            roomName=self._contrib.getRoom().getName()
        vars["defaultInheritPlace"]=defaultInheritPlace
        vars["defaultDefinePlace"]=defaultDefinePlace
        vars["confPlace"]=""
        confLocation=self._contrib.getOwner().getLocation()
        if self._contrib.isScheduled():
            confLocation=self._contrib.getSchEntry().getSchedule().getOwner().getLocation()
            sDate=self._contrib.getAdjustedStartDate()
            vars["sYear"]=quoteattr(str(sDate.year))
            vars["sMonth"]=quoteattr(str(sDate.month))
            vars["sDay"]=quoteattr(str(sDate.day))
            vars["sHour"]=quoteattr(str(sDate.hour))
            vars["sMinute"]=quoteattr(str(sDate.minute))
            vars["startDate"]=self._contrib.getAdjustedStartDate().strftime("%Y-%b-%d %H:%M")
        else:
            vars["sYear"]=quoteattr(str(""))
            vars["sMonth"]=quoteattr(str(""))
            vars["sDay"]=quoteattr(str(""))
            vars["sHour"]=quoteattr(str(""))
            vars["sMinute"]=quoteattr(str(""))
            vars["startDate"]= _("""--_("not scheduled")--""")
        vars["durHours"]=quoteattr(str((datetime(1900,1,1)+self._contrib.getDuration()).hour))
        vars["durMins"]=quoteattr(str((datetime(1900,1,1)+self._contrib.getDuration()).minute))
        if confLocation:
            vars["confPlace"]=confLocation.getName()
        vars["locationName"]=locationName
        vars["locationAddress"]=locationAddress
        vars["defaultInheritRoom"]=defaultInheritRoom
        vars["defaultDefineRoom"]=defaultDefineRoom
        vars["confRoom"]=""
        confRoom=self._contrib.getOwner().getRoom()
        if self._contrib.isScheduled():
            confRoom=self._contrib.getSchEntry().getSchedule().getOwner().getRoom()
        if confRoom:
            vars["confRoom"]=confRoom.getName()
        vars["roomName"]=roomName
        vars["parentType"]="conference"
        if self._contrib.getSession() is not None:
            vars["parentType"]="session"
            if self._contrib.isScheduled():
                vars["parentType"]="session slot"
        vars["boardNumber"]=quoteattr(str(self._contrib.getBoardNumber()))
        return vars


class WPModContribListEditContrib(WPModContribList):

    def __init__(self,rh,contrib):
        WPModContribList.__init__(self,rh,contrib.getSession())
        self._contrib=contrib

    def _getTabContent( self, params ):
        wc=WSessionModContribListEditContrib(self._contrib)
        return wc.getHTML({"sortBy":params.get("sortBy",""),
                            "postURL":urlHandlers.UHSessionModContribListEditContrib.getURL(self._contrib)})


class WSessionModAddContribs(wcomponents.WTemplated):

    def __init__(self,session):
        self._session=session

    def _getTrackItems(self):
        res=[ _("""<option value="--none--">--_("none")--</option>""")]
        for track in self._session.getConference().getTrackList():
            res.append("""<option value=%s>(%s) %s</option>"""%(quoteattr(str(track.getId())),self.htmlText(track.getCode()),self.htmlText(track.getTitle())))
        return "".join(res)

    def _getContribItems(self):
        res=[]
        #available contributions to a session are those contributions which:
        #   1) are not included in any session
        #   2) are not withdrawn
        #   3) are not scheduled
        sc=contribFilters.SortingCriteria(["number"])
        contribList=filters.SimpleFilter(None,sc).apply(self._session.getConference().getContributionList())
        for contrib in contribList:
            if contrib.getSession() is not None or isinstance(contrib.getCurrentStatus(),conference.ContribStatusWithdrawn) or contrib.isScheduled():
                continue
            cType=""
            if contrib.getType() is not None:
                cType="%s"%contrib.getType().getName()
            spks=[self.htmlText(spk.getFullName()) for spk in contrib.getSpeakerList()]
            res.append("""
                <tr>
                    <td valgin="top"><input type="checkbox" name="manSelContribs" value=%s></td>
                    <td valgin="top">%s</td>
                    <td valgin="top">[%s]</td>
                    <td valgin="top"><i>%s</i></td>
                    <td valgin="top">%s</td>
                </tr>
                        """%(quoteattr(str(contrib.getId())), \
                        self.htmlText(contrib.getId()),\
                        self.htmlText(cType), \
                        self.htmlText(contrib.getTitle()),\
                        "<br>".join(spks)))
        return "".join(res)

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        vars["postURL"]=quoteattr(str(urlHandlers.UHSessionModAddContribs.getURL(self._session)))
        vars["tracks"]=self._getTrackItems()
        vars["availContribs"]=self._getContribItems()
        return vars


class WPModAddContribs(WPModContribList):

    def _getTabContent( self, params ):
        wc=WSessionModAddContribs(self._session)
        return wc.getHTML()


class WPModImportContribsConfirmation(WPModContribList):

    def _getTabContent( self, params ):
        wc=wcomponents.WConfModMoveContribsToSessionConfirmation(self._conf,params.get("contribIds",[]),self._session)
        p={"postURL":urlHandlers.UHSessionModAddContribs.getURL(self._session)}
        return wc.getHTML(p)


class WPModParticipantList( WPSessionModifBase ):

    def __init__(self, rh, conf, emailList, displayedGroups, contribs):
        WPSessionModifBase.__init__(self, rh, conf)
        self._emailList = emailList
        self._displayedGroups = displayedGroups
        self._contribs = contribs

    def _getBody( self, params ):
        WPSessionModifBase._getBody(self, params)
        wc = WContribParticipantList(self._conf, self._emailList, self._displayedGroups, self._contribs)
        params = {"urlDisplayGroup":urlHandlers.UHSessionModParticipantList.getURL(self._session)}
        return wc.getHTML(params)

class WPSessionDisplayRemoveMaterialsConfirm( WPSessionDefaultDisplayBase ):

    def __init__(self,rh, conf, mat):
        WPSessionDefaultDisplayBase.__init__(self,rh,conf)
        self._mat=mat

    def _getBody(self,params):
        wc=wcomponents.WDisplayConfirmation()
        msg="""Are you sure you want to delete the following material?<br>
        <b><i>%s</i></b>
        <br>"""%self._mat.getTitle()
        url=urlHandlers.UHSessionDisplayRemoveMaterial.getURL(self._mat.getOwner())
        return wc.getHTML(msg,url,{"deleteMaterial":self._mat.getId()})

class WPSessionDisplayWriteMinutes( WPSessionDefaultDisplayBase ):

    def _getBody( self, params ):
        wc = wcomponents.WWriteMinutes( self._session )
        pars = {"postURL": urlHandlers.UHSessionDisplayWriteMinutes.getURL(self._session) }
        return wc.getHTML( pars )

class WPSessionModifRelocate(WPSessionModifBase):

    def __init__(self, rh, session, entry, targetDay):
        WPSessionModifBase.__init__(self, rh, session)
        self._targetDay=targetDay
        self._entry=entry

    def _getPageContent( self, params):
        wc=wcomponents.WSchRelocate(self._entry)
        p={"postURL":quoteattr(str(urlHandlers.UHSessionModifScheduleRelocate.getURL(self._entry))), \
                "targetDay":quoteattr(str(self._targetDay))}
        return wc.getHTML(p)


class WPSessionModifMaterials( WPSessionModifBase ):

    def __init__(self, rh, session):
        self._target = session
        WPSessionModifBase.__init__(self, rh, session)

    def _setActiveTab( self ):
        self._tabMaterials.setActive()

    ## def _getContent( self, pars ):
    ##     wc=wcomponents.WShowExistingMaterial(self._target)
    ##     return wc.getHTML( pars )

    def _getTabContent( self, pars ):
        wc=wcomponents.WShowExistingMaterial(self._target)
        return wc.getHTML( pars )

    def _includeFavList(self):
        return True

class WPSessionDatesModification(WPSessionModifSchedule):

    def _getTabContent(self,params):
        p=WSessionModEditDates(self._session.getConference())
        params["postURL"]=urlHandlers.UHSessionDatesModification.getURL(self._session)
        return p.getHTML(params)

class WSessionModEditDates(wcomponents.WTemplated):

    def __init__(self,targetConf,targetDay=None):
        self._conf=targetConf
        self._targetDay=targetDay

    def _getErrorHTML(self,l):
        if len(l)>0:
            return """
                <tr>
                    <td colspan="2" align="center">
                        <br>
                        <table bgcolor="red" cellpadding="6">
                            <tr>
                                <td bgcolor="white" style="color: red">%s</td>
                            </tr>
                        </table>
                        <br>
                    </td>
                </tr>
                    """%"<br>".join(l)
        else:
            return ""

    def getVars( self ):
        vars=wcomponents.WTemplated.getVars(self)
        vars["errors"]=self._getErrorHTML(vars.get("errors",[]))
        vars["postURL"]=quoteattr(str(vars["postURL"]))
        vars["calendarIconURL"]=Config.getInstance().getSystemIconURL( "calendar" )
        vars["calendarSelectURL"]=urlHandlers.UHSimpleCalendar.getURL()
        refDate=self._conf.getSchedule().calculateDayEndDate(self._targetDay, self._conf.getTimezone())
        endDate = None
        if refDate.hour == 23:
            refDate = refDate - timedelta(minutes=refDate.minute)
            endDate = refDate + timedelta(minutes=59)
        vars["sDay"]=quoteattr(str(vars.get("sDay",refDate.day)))
        vars["sMonth"]=quoteattr(str(vars.get("sMonth",refDate.month)))
        vars["sYear"]=quoteattr(str(vars.get("sYear",refDate.year)))
        vars["sHour"]=quoteattr(str(vars.get("sHour",refDate.hour)))
        vars["sMinute"]=quoteattr(str(vars.get("sMinute",refDate.minute)))
        if not endDate:
            endDate=refDate+timedelta(hours=1)
        vars["eDay"]=quoteattr(str(vars.get("eDay",endDate.day)))
        vars["eMonth"]=quoteattr(str(vars.get("eMonth",endDate.month)))
        vars["eYear"]=quoteattr(str(vars.get("eYear",endDate.year)))
        vars["eHour"]=quoteattr(str(vars.get("eHour",endDate.hour)))
        vars["eMinute"]=quoteattr(str(vars.get("eMinute",endDate.minute)))
        vars["autoUpdate"]=""
        if not self._conf.getEnableSessionSlots():
            vars["disabled"] = "disabled"
        else:
            vars["disabled"] = ""
        vars["adjustSlots"]=""
        return vars

