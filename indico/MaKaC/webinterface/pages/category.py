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

from copy import copy
from operator import attrgetter

from flask import session
from datetime import timedelta, datetime
from time import mktime, strptime
import os
import calendar
import MaKaC.webinterface.pages.main as main
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.wcomponents as wcomponents
from MaKaC.webinterface.wcalendar import Overview
import MaKaC.conference as conference
from MaKaC.conference import CategoryManager
from indico.core.config import Config
import MaKaC.webinterface.wcalendar as wcalendar
from MaKaC.webinterface.pages.metadata import WICalExportBase
import MaKaC.common.info as info
from MaKaC.i18n import _
from indico.modules.events.util import preload_events
from indico.modules.users.legacy import AvatarUserWrapper
from indico.modules.groups.legacy import GroupWrapper
from indico.util.date_time import format_time
from indico.util.i18n import i18nformat

from MaKaC.webinterface.common.timezones import TimezoneRegistry
from MaKaC.common.timezoneUtils import DisplayTZ, nowutc
from pytz import timezone
from MaKaC.common.TemplateExec import truncateTitle

from MaKaC.common.fossilize import fossilize

from indico.core.index import Catalog
from indico.modules import ModuleHolder
from indico.modules.events.layout import theme_settings
from indico.modules.events.timetable.models.entries import TimetableEntryType
from indico.modules.upcoming import WUpcomingEvents
from indico.web.flask.templating import get_template_module
from indico.web.flask.util import url_for
from indico.web.menu import render_sidemenu


def format_location(item):
    if item.inherit_location or not item.has_location_info:
        return u''
    tpl = get_template_module('events/display/indico/_common.html')
    return tpl.render_location(item)


class WPCategoryBase (main.WPMainBase):
    def __init__(self, rh, categ, **kwargs):
        main.WPMainBase.__init__(self, rh, **kwargs)
        self._target = categ
        title = "Indico"
        if self._target:
            title = "Indico [%s]"%(self._target.getName() )
        self._setTitle(title)
        self._conf = None

    def getCSSFiles(self):
        return main.WPMainBase.getCSSFiles(self) + self._asset_env['category_sass'].urls()

    def _currentCategory(self):
        return self._target


class WPCategoryDisplayBase(WPCategoryBase):
    pass


class WCategoryDisplay(WICalExportBase):

    def __init__(self, target, wfReg, tz):
        self._target = target
        self._wfReg = wfReg
        self._timezone = timezone(tz)

    def getHTML(self, aw, params):
        self._aw = aw
        return wcomponents.WTemplated.getHTML(self, params)

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        isRootCategory = self._target.getId() == "0"

        vars["name"] = self._target.getName()
        vars["description"] = self._target.getDescription()
        vars["categ"] = vars["target"] = self._target
        vars["urlICSFile"] = url_for('category.categoryDisplay-ical', self._target)
        vars["isRootCategory"] = isRootCategory
        vars["timezone"] = self._timezone
        subcats = self._target.subcategories

        confs = self._target.conferences
        if subcats:
            cl = wcomponents.WCategoryList(self._target)
            params = {"categoryDisplayURLGen": vars["categDisplayURLGen"]}
            vars["contents"] = cl.getHTML( self._aw, params )
        elif confs:
            pastEvents = session.get('fetchPastEventsFrom', set())
            showPastEvents = (self._target.getId() in pastEvents or
                             (session.user and session.user.settings.get('show_past_events')))
            cl = wcomponents.WConferenceList(self._target, self._wfReg, showPastEvents)
            params = {"conferenceDisplayURLGen": vars["confDisplayURLGen"]}
            vars["contents"] = cl.getHTML( self._aw, params )
        else:
            cl = wcomponents.WEmptyCategory()
            vars["contents"] = cl.getHTML( self._aw )

        mgrs = []
        for mgr in self._target.getManagerList():
            if isinstance(mgr, AvatarUserWrapper):
                mgrs.append(("avatar", mgr.getAbrName()))
            elif isinstance(mgr, GroupWrapper):
                mgrs.append(("group", mgr.getName()))

        vars["managers"] = sorted(mgrs)

        # Export ICS
        if self._target.conferences:
            vars.update(self._getIcalExportParams(self._aw.getUser(), '/export/categ/%s.ics' % self._target.getId(), {'from':"-7d"}))

        vars["isLoggedIn"] = self._aw.getUser() is not None

        minfo = info.HelperMaKaCInfo.getMaKaCInfoInstance()
        vars["isNewsActive"] = minfo.isNewsActive()

        # if this is the front page, include the
        # upcoming event information (if there are any)
        if isRootCategory:
            upcoming = ModuleHolder().getById('upcoming_events')
            upcoming_list = upcoming.getUpcomingEventList()
            if upcoming_list:
                vars["upcomingEvents"] = WUpcomingEvents(self._timezone, upcoming_list).getHTML(vars)
            else:
                vars["upcomingEvents"] = ''

        return vars


class WPCategoryDisplay(WPCategoryDisplayBase):

    def __init__(self, rh, target, wfReg):
        WPCategoryDisplayBase.__init__(self, rh, target)
        self._wfReg = wfReg
        tzUtil = DisplayTZ(self._getAW(), target)  # None,useServerTZ=1)
        self._locTZ = tzUtil.getDisplayTZ()

    def _getHeadContent(self):
        # add RSS feed
        url = url_for('category.categoryDisplay-atom', self._target)

        return WPCategoryDisplayBase._getHeadContent( self ) + \
        i18nformat("""<link rel="alternate" type="application/atom+xml" title="_('Indico Atom Feed')" href="%s">""") % url

    def _getBody( self, params ):
        wc = WCategoryDisplay(self._target, self._wfReg, self._locTZ)
        pars = { "categDisplayURLGen": urlHandlers.UHCategoryDisplay.getURL, \
                "confDisplayURLGen": urlHandlers.UHConferenceDisplay.getURL, \
                "allowUserModif": self._target.canModify( self._getAW() ), \
                "allowCreateEvent": self._target.canCreateConference(self._getAW().getUser()) }
        page = wc.getHTML( self._getAW(), pars )
        return page

    def _getNavigationDrawer(self):
        pars = {"target": self._target, "isModif": False}
        return wcomponents.WNavigationDrawer( pars )

class WOverviewBreak( wcomponents.WTemplated ):

    def __init__( self, aw, entry ):
        self._break = entry
        self._aw = aw

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["startTime"] = format_time(self._break.timetable_entry.start_dt)
        vars["title"] = self._break.title
        return vars


class WOverviewContribBase(wcomponents.WTemplated):

    def __init__(self, aw, contrib, date, details="conference"):
        self._aw = aw
        self._contrib = contrib
        self._date = date
        self._details = details

    def _getSpeakerText(self):
        speakers = [link.person.get_full_name(abbrev_first_name=True, last_name_upper=False)
                    for link in self._contrib.person_links if link.is_speaker]
        if speakers:
            return u'({})'.format(u'; '.join(speakers))
        else:
            return ''

    def getHTML(self, params={}):
        return wcomponents.WTemplated.getHTML(self, params)

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["timezone"] = DisplayTZ(self._aw).getDisplayTZ()
        vars["startTime"] = format_time(self._contrib.timetable_entry.start_dt)
        vars["title"] = self._contrib.title
        vars["speakers"] = self._getSpeakerText()
        vars["location"] = format_location(self._contrib)
        return vars


class WOverviewContribFullDisplay( WOverviewContribBase ):
    pass


class WOverviewContribMinDisplay( WOverviewContribBase ):
    pass


class WOverviewContribution:
    def __init__( self, aw, contrib, date, details="conference" ):
        self._comp = None

        """ This is needed for the future? The two
            templates are currently identical """

        if contrib.can_access(session.user):
            self._comp = WOverviewContribFullDisplay(aw, contrib, date, details)
        else:
            self._comp = WOverviewContribMinDisplay(aw, contrib, date, details)

    def getHTML(self, params={}):
        if not self._comp:
            return ""
        return self._comp.getHTML(params)


class WOverviewSessionBase( wcomponents.WTemplated ):

    def __init__( self, aw, session, date, details="conference" ):
        self._aw = aw
        self._session = session
        self._date = date
        self._details = details

    def _getConvenerText(self):
        conveners = [link.person.full_name for block in self._session.blocks for link in block.person_links]
        return u"({})".format(u"; ".join(conveners))

    def _getDetails(self):
        if self._details != "contribution":
            return ""
        res = []
        entries = [block.timetable_entries.filter_by(start_dt=self._date) for block in self._session.blocks]
        for entry in entries:
            if self._details == "contribution":
                if entry.type == TimetableEntryType.CONTRIBUTION:
                    wc = WOverviewContribution(self._aw, entry.getOwner(), self._date, self._details)
                    res.append(wc.getHTML())
                elif entry.type == TimetableEntryType.BREAK:
                    res.append(self._getBreakItem(entry))
        return u"".join(res)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        tz = DisplayTZ(self._aw).getDisplayTZ()
        vars["startTime"] = format_time(self._slot.timetable_entry.start_dt.astimezone(timezone(tz)))
        conf = self._session.event_new
        import MaKaC.webinterface.webFactoryRegistry as webFactoryRegistry
        wr = webFactoryRegistry.WebFactoryRegistry()
        wf = wr.getFactory(conf)
        if wf != None:
            type = wf.getId()
        else:
            type = "conference"
        if type != 'meeting':
            vars["title"] = self._session.title
            vars["titleUrl"] = None
        else:
            vars["title"] = self._session.title
            vars["titleUrl"] = '{}#{}'.format(urlHandlers.UHConferenceDisplay.getURL(conf), self._session.id)
        vars["conveners"] = self._getConvenerText()
        vars["location"] = format_location(self._session)
        vars["details"] = self._getDetails()
        return vars

class WOverviewSessionSlot(WOverviewSessionBase):

    def __init__(self, aw, slot, date, details="conference"):
        self._aw = aw
        self._session = slot.session
        self._slot = slot
        self._date = date
        self._details = details

    def _getDetails(self):
        if self._details != "contribution":
            return ""

        res = []
        for entry in self._slot.timetable_entry.children:
            if entry.start_dt < self._date or entry.start_dt - self._date > timedelta(days=1):
                continue
            if entry.type == TimetableEntryType.CONTRIBUTION:
                wc = WOverviewContribution(self._aw, entry.object, self._date, self._details)
                res.append(wc.getHTML())
            elif entry.type == TimetableEntryType.BREAK:
                wc = WOverviewBreak(self._aw, entry.object)
                res.append(wc.getHTML())
        return "".join(res)

class WOverviewSessionFullDisplay( WOverviewSessionBase ):
    pass


class WOverviewSessionMinDisplay( WOverviewSessionBase ):

    def _getBreakItem( self, entry ):
        return ""


class WOverviewSession:

    def __init__( self, aw, session, date, details="conference" ):
        self._comp = None
        if session.canAccess( aw ):
            self._comp = WOverviewSessionFullDisplay( aw, \
                                                    session, \
                                                    date, \
                                                    details )
        else:
            self._comp = WOverviewSessionMinDisplay( aw, \
                                                    session, \
                                                    date, \
                                                    details )
    def getHTML( self, params ):
        if not self._comp:
            return ""
        return self._comp.getHTML( params )


class WOverviewConfBase( wcomponents.WTemplated ):

    def __init__(self, aw, conference, date, url, icons, data, details='conference', startTime=None):
        self._conf = conference
        self._url = url
        self._aw = aw
        self._details = details
        self._date = date
        self._icons = icons
        self._startTime = startTime
        self._data = data

    def _getChairText( self ):
        items = []
        if self._conf.getChairmanText():
            items.append(self._conf.getChairmanText())
        for p in sorted(self._conf.as_event.person_links, key=attrgetter('full_name')):
            items.append(p.full_name.encode('utf-8'))
        return '({})'.format('; '.join(items)) if items else ''

    def _getDetails(self):
        if self._details == "conference":
            return ""
        res = []
        blocks, contribs, breaks = self._data['blocks'], self._data['contribs'], self._data['breaks']
        day = self._date.date()

        if self._details == 'session':
            for tt_entry, block in blocks[day]:
                wc = WOverviewSessionSlot(self._aw, block, self._date, self._details)
                res.append(wc.getHTML())
        elif self._details == 'contribution':
            for tt_entry, obj in sorted(blocks[day] + contribs[day] + breaks[day], key=lambda x: x[0].start_dt):
                if tt_entry.type == TimetableEntryType.SESSION_BLOCK:
                    wc = WOverviewSessionSlot(self._aw, obj, self._date, self._details)
                    res.append(wc.getHTML())
                elif tt_entry.type == TimetableEntryType.CONTRIBUTION and tt_entry.parent_id is None:
                    wc = WOverviewContribution(self._aw, obj, self._date, self._details)
                    res.append(wc.getHTML())
                elif tt_entry.type == TimetableEntryType.BREAK and tt_entry.parent_id is None:
                    wc = WOverviewBreak(self._aw, obj)
                    res.append(wc.getHTML())
        return "".join(res)

    def _getIcon( self ):
        confid = self._conf.as_event.id
        iconHtml = ""
        for icon in self._icons.keys():
            if confid in self._icons[icon]:
                cm=CategoryManager()
                categ = cm.getById(str(icon))
                iconHtml += """<img src="%s" width="16" height="16" alt="categ" onmouseover="IndicoUI.Widgets.Generic.tooltip(this, event, '%s')" />""" %(urlHandlers.UHCategoryIcon.getURL(categ), categ.getName())
        return iconHtml

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        tz = timezone(DisplayTZ(session.user, None, useServerTZ=True).getDisplayTZ())
        if self._startTime:
            vars["startTime"] = format_time(self._startTime.astimezone(tz))
        else:
            vars["startTime"] = _("Ongoing")
        vars["timezone"] = tz
        vars["title"] = self._conf.getTitle()
        if self._conf.isProtected():
            vars["title"] += """&nbsp;<img src=%s style="vertical-align: middle; border: 0;">""" % Config.getInstance().getSystemIconURL("protected")
        vars["url"] = self._url
        vars["chairs"] = self._getChairText()
        vars["location"] = format_location(self._conf.as_event)
        vars["details"] = self._getDetails()
        vars["icon"] = self._getIcon()
        return vars


class WOverviewConfFullDisplay( WOverviewConfBase ):
    pass

class WOverviewConfMinDisplay( WOverviewConfBase ):

    def _getDetails( self ):
        return ""

    def _getBreakItem( self, entry ):
        return ""


class WOverviewConferenceItem:

    def __init__(self, aw, conference, date, displayURL, icons, data, details="conference", startTime = None):
        self._comp = None
        if details=="conference" or conference.canAccess( aw ):
            self._comp = WOverviewConfFullDisplay( aw, \
                                                    conference, \
                                                    date, \
                                                    displayURL, \
                                                    icons, \
                                                    data,
                                                    details,
                                                    startTime )
        else:
            self._comp = WOverviewConfMinDisplay( aw, \
                                                    conference, \
                                                    date, \
                                                    displayURL, \
                                                    icons, \
                                                    data,
                                                    details,
                                                    startTime )

    def getHTML( self, params ):
        if not self._comp:
            return ""
        return self._comp.getHTML( params )


class WDayOverview(wcomponents.WTemplated):

    def __init__(self, ow):
        self._ow = ow
        self._categ_list = ow.getCategoryList()
        self._day = ow.getDate()

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        prevOW = self._ow.getOverviewPrevPeriod()
        prevsel = urlHandlers.UHCategoryOverview.getURLFromOverview( prevOW )
        nextOW = self._ow.getOverviewNextPeriod()
        nextsel = urlHandlers.UHCategoryOverview.getURLFromOverview( nextOW )
        pprevOW = self._ow.getOverviewPrevBigPeriod()
        pprevsel = urlHandlers.UHCategoryOverview.getURLFromOverview( pprevOW )
        nnextOW = self._ow.getOverviewNextBigPeriod()
        nnextsel = urlHandlers.UHCategoryOverview.getURLFromOverview( nnextOW )
        vars["date"] = """<a href="%s">&lt;&lt;</a>&nbsp;&nbsp;<a href="%s">&lt;</a>&nbsp;&nbsp;%s&nbsp;&nbsp;<a href="%s">&gt;</a>&nbsp;&nbsp;<a href="%s">&gt;&gt;</a>""" % (\
                pprevsel, \
                prevsel,\
                self._ow.getDate().strftime("%A %d %B %Y"), \
                nextsel,\
                nnextsel)
        segments = []
        detailed_data = self._ow.getData()
        icons = self._ow.getIcons()

        for tt_start_dt, event in sorted(detailed_data['events'][self._day.date()]):
            oi = WOverviewConferenceItem(self._ow.getAW(),
                                         event.as_legacy,
                                         self._ow.getDate(),
                                         url_for('event.conferenceDisplay', event),
                                         icons,
                                         detailed_data[event.id],
                                         self._ow.getDetailLevel(),
                                         tt_start_dt)
            segments.append(oi.getHTML({}))

        for event in detailed_data['ongoing_events']:
            oi = WOverviewConferenceItem(self._ow.getAW(),
                                         event.as_legacy,
                                         self._ow.getDate(),
                                         url_for('event.conferenceDisplay', event),
                                         icons,
                                         detailed_data[event.id],
                                         self._ow.getDetailLevel(),
                                         None)
            segments.append(oi.getHTML({}))

        if not detailed_data['events']:
            segments.append(_("There are no events on the selected day"))
        vars["items"] = "".join(segments)
        return vars


class WWeekOverview(wcomponents.WTemplated):

    def __init__( self, ow ):
        self._categ_list = ow.getCategoryList()
        self._ow = ow

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        isWeekendFree = True
        prevOW = self._ow.getOverviewPrevPeriod()
        prevsel = urlHandlers.UHCategoryOverview.getURLFromOverview( prevOW )
        nextOW = self._ow.getOverviewNextPeriod()
        nextsel = urlHandlers.UHCategoryOverview.getURLFromOverview( nextOW )

        startDate = """<a href="%s">&lt;</a>&nbsp;&nbsp;%s""" % (\
                prevsel,\
                self._ow.getStartDate().strftime("%A %d %B %Y"))
        endDate = """%s&nbsp;&nbsp;<a href="%s">&gt;</a>""" %(\
                self._ow.getEndDate().strftime("%A %d %B %Y"),\
                nextsel)
        vars["dates"] = """%s &nbsp;&ndash;&nbsp; %s"""%(startDate, endDate)

        detailed_data = self._ow.getData()
        icons = self._ow.getIcons()
        inc = timedelta(1)
        sd = self._ow.getStartDate()
        idx = 0
        while sd <= self._ow.getEndDate():
            weekend = sd.weekday() >= 5
            vars["date%i" % idx] = sd.strftime("%a %d/%m")
            res = []
            for start_dt, event in sorted(detailed_data['events'][sd.date()]):
                wc = WOverviewConferenceItem(self._ow.getAW(), event.as_legacy, sd,
                                             url_for('event.conferenceDisplay', event), icons,
                                             detailed_data[event.id], self._ow.getDetailLevel(), start_dt)
                res.append(wc.getHTML({}))
            if not res:
                res.append("<tr><td></td></tr>")
            elif weekend:
                isWeekendFree = False
            vars["item%i" % idx] = "".join(res)
            sd += inc
            idx += 1
        vars["isWeekendFree"] = isWeekendFree
        return vars


class WMonthOverview(wcomponents.WTemplated):

    def __init__(self, ow):
        self._ow = ow
        self._categ_list = ow.getCategoryList()
        self._isWeekendFree = True
        self._detailed_data = self._ow.getData()
        self._icons = self._ow.getIcons()

    def _getDayCell(self, day):
        res = []
        for tt_start_dt, event in sorted(self._detailed_data['events'][day.getDate().date()]):
            wc = WOverviewConferenceItem(self._ow.getAW(),
                                         event.as_legacy,
                                         day.getDate(),
                                         url_for('event.conferenceDisplay', event),
                                         self._icons,
                                         self._detailed_data[event.id],
                                         self._ow.getDetailLevel(),
                                         tt_start_dt)
            res.append(wc.getHTML({}))
        return "".join(res)

    def _getMonth( self ):
        dayList = [[]]
        numWeek=0

        dl = self._ow.getDayList()
        for i in range(dl[0].getWeekDay()):
            dayList[numWeek].append(None)
        for day in dl:
            dayList[numWeek].append(day)
            if day.getWeekDay() >= 5:
                if day.getWeekDay() == 6:
                    numWeek +=1
                    dayList.append([])

        for i in range( 6-dl[-1].getWeekDay() ):
            dayList[numWeek].append(None)
        return dayList


    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        prevOW = self._ow.getOverviewPrevPeriod()
        prevsel = urlHandlers.UHCategoryOverview.getURLFromOverview( prevOW )
        nextOW = self._ow.getOverviewNextPeriod()
        nextsel = urlHandlers.UHCategoryOverview.getURLFromOverview( nextOW )
        pprevOW = self._ow.getOverviewPrevBigPeriod()
        pprevsel = urlHandlers.UHCategoryOverview.getURLFromOverview( pprevOW )
        nnextOW = self._ow.getOverviewNextBigPeriod()
        nnextsel = urlHandlers.UHCategoryOverview.getURLFromOverview( nnextOW )
        startDate = """<a href="%s">&lt;&lt;</a>&nbsp;&nbsp;<a href="%s">&lt;</a>&nbsp;&nbsp;&nbsp;%s""" % (\
                pprevsel,\
                prevsel,\
                self._ow.getStartDate().strftime("%A %d %B %Y"))
        endDate = """%s&nbsp;&nbsp;&nbsp;<a href="%s">&gt;</a>&nbsp;&nbsp;<a href="%s">&gt;&gt;</a>""" %(\
                self._ow.getEndDate().strftime("%A %d %B %Y"),\
                nextsel,\
                nnextsel)
        vars["dates"] = """%s &nbsp;&ndash;&nbsp; %s"""%(startDate, endDate)

        dayNames = [ _("Monday"), _("Tuesday"), _("Wednesday"), _("Thursday"), _("Friday"), \
                        _("Saturday"), _("Sunday") ]
        #if calendar.SUNDAY == calendar.firstweekday():
        #    dayNames.remove( "Sunday" )
        #    dayNames.insert( "0", "Sunday" )
        for name in dayNames:
            vars["nameDay%i"%dayNames.index(name)] = name
        self._displayConfURLGen = vars["displayConfURLGen"]
        vars["month"] = self._getMonth()
        vars["isWeekendFree"] = self._isWeekendFree
        vars["getDayCell"] = lambda day: self._getDayCell(day)
        return vars


class WCategoryOverview(wcomponents.WTemplated):

    def __init__( self, ow, aw ):
        self._categ = ow.getCategoryList()[0]
        self._ow = ow
        self._aw = aw

    def _getDetailLevelOpts( self ):
        l = []
        for dl in self._ow.getAllowedDetailLevels():
            selected = ""
            if dl == self._ow.getDetailLevel():
                selected = "selected"
            if dl == "conference":
                dltext = "agenda"
            else:
                dltext = dl
            l.append("""<option value="%s" %s>%s</option>"""%( dl, selected, dltext ))
        return "".join(l)

    def _getKey( self, vars):
        l = []
        icons = self._ow.getIcons().keys()
        if len(icons) > 0:
            for icon in icons:
                cm= CategoryManager()
                categ=cm.getById(str(icon))
                otherOW = self._ow.getOverviewOtherCateg(categ)
                a=(""" <a href="%s" style="font-size: 1.0em;" onmouseover="IndicoUI.Widgets.Generic.tooltip(this, event, '%s')"><img src="%s" width="16" height="16" border="0">&nbsp;%s</a>  <br/>""" %(
                                        vars["categOverviewURLGen"]( otherOW ),
                                        categ.getName(),
                                        urlHandlers.UHCategoryIcon.getURL(categ),
                                        truncateTitle(categ.getName(), 20)))
                if not a in l:
                    l.append(a)
        return "". join(l)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        l = self._ow.getLocator()
        del l["detail"]
        del l["period"]
        del l["day"]
        del l["month"]
        del l["year"]

        vars["selDay"] = ""
        vars["selWeek"] = ""
        vars["selMonth"] = ""
        vars["selYear"] = ""

        vars["detailLevelOpts"] = self._getDetailLevelOpts()

        if isinstance( self._ow, wcalendar.MonthOverview ):
            displayOW = WMonthOverview( self._ow )
            vars["selMonth"] = "selected"
        elif isinstance( self._ow, wcalendar.WeekOverview ):
            displayOW = WWeekOverview( self._ow )
            vars["selWeek"] = "selected"
        else:
            displayOW = WDayOverview(self._ow)
            vars["selDay"] = "selected"

        p = { "displayConfURLGen": vars["displayConfURLGen"] }
        vars["overview"] = displayOW.getHTML( p )

        vars["locator"] = l.getWebForm()
        vars["key"] = self._getKey(vars)

        vars["day"] = self._ow.getDate().day
        vars["month"] = self._ow.getDate().month
        vars["year"] = self._ow.getDate().year

        return vars

    def _getWeekDays(self):
        """returns a list with the current week days"""

        year=int(self._ow.getDate().year)
        month=int(self._ow.getDate().month)
        day=int(self._ow.getDate().day)
        daynumber=int(calendar.weekday(year,month,day))

        date = self._ow.getDate() - timedelta(daynumber)
        delta = timedelta(1)
        res = []
        for i in range(7):
            res.append((str(date.day)+"-"+str(date.month)+"-"+str(date.year)))
            date += delta

        return res




    def _getNextWeekDays(self):


        y=int(self._ow.getDate().year)
        m=int(self._ow.getDate().month)
        d=int(self._ow.getDate().day)

        res=[]
        i=0
        while i<=6:

            if (d+i)<=31 and (m==8 or m==1 or m==3 or m==5 or m==7 or m==10):
                res+=[str(d+i)+"-"+str(m)+"-"+str(y)]
            if (d+i)<=30 and (m==4 or m==6 or m==9 or m==11):
                res+=[str(d+i)+'-'+str(m)+'-'+str(y)]
            if (d+i)<=28 and m==2 and ((y%4!=0) or (y %4 ==0 and y %100==0)):
                res+=[(str(d+i)+"-"+str(m)+"-"+str(y))]
            if (d+i)<30 and m==2 and ((y%4==0 and y%100!=0) or y%400==0):
                res+=[(str(d+i)+"-"+str(m)+"-"+str(y))]
            i+=1

        j=0
        if d<7 and len(res)<7:
            while j<(7-len(res)):
                res+=[(str(d+i+j)+"-"+str(m)+"-"+str(y))]
                j+=1


        return res

    def _whichPeriod(self, vars):
        if vars["selDay"] == "selected":
            return "day"
        if vars["selWeek"] == "selected":
            return "week"
        if vars["selMonth"] == "selected":
            return "month"

    def _getMonthDays(self):
        year=int(self._ow.getDate().year)
        month=int(self._ow.getDate().month)
        res=[]
        for day in range(1,calendar.monthrange(year,month)[1]+1):
            res+=[str(day)+'-'+str(month)+'-'+str(year)]

        return res

class WPCategOverview( WPCategoryDisplayBase ):

    def __init__( self, rh, categ, ow ):
        WPCategoryDisplayBase.__init__( self, rh, categ )
        self._ow = ow
        self._categ = categ
        self._locTZ = DisplayTZ(self._getAW(),None,useServerTZ=1).getDisplayTZ()

    def _getTitle(self):
        return WPCategoryDisplayBase._getTitle(self) + " - " + _("Events Display")

    def _getHeadContent( self ):
        # add RSS feed
        if self._ow.getDate().date() == nowutc().astimezone(timezone(self._locTZ)).date():
            url = url_for('category.categoryDisplay-atom', self._categ)
            return i18nformat("""<link rel="alternate" type="application/rss+xml" title= _("Indico RSS Feed") href="%s">""") % url
        return ""

    def _getBody(self, params):
        if (self._categ.getId() == "0" and type(self._ow) is Overview and
                self._ow.getDate().date() == nowutc().astimezone(timezone(self._locTZ)).date()):
            path = os.path.join(Config.getInstance().getXMLCacheDir(), "categOverview")
            currenttime = int(mktime(strptime(
                (datetime.now() - timedelta(minutes=60)).strftime("%a %b %d %H:%M:%S %Y"))))
            if os.path.exists(path) and os.path.getmtime(path) > currenttime:
                fp = file(path, 'rb')
                cache = fp.read()
                fp.close()
                return cache
            else:
                wc = WCategoryOverview( self._ow, self._rh.getAW())
                pars = { "postURL": urlHandlers.UHCategoryOverview.getURL(), \
                "displayConfURLGen": urlHandlers.UHConferenceDisplay.getURL, \
                "categOverviewURLGen": urlHandlers.UHCategoryOverview.getURLFromOverview }
                cache = wc.getHTML( pars )
                fp = file(path, 'wb')
                fp.write(cache)
                fp.close()
                return cache
        else:
            wc = WCategoryOverview( self._ow, self._rh.getAW())
            pars = { "postURL": urlHandlers.UHCategoryOverview.getURL(), \
                     "displayConfURLGen": urlHandlers.UHConferenceDisplay.getURL, \
                     "categDisplayURL": urlHandlers.UHCategoryDisplay.getURL(self._categ), \
                     "categOverviewURLGen": urlHandlers.UHCategoryOverview.getURLFromOverview, \
                     "categoryTitle": self._categ.getTitle() }
            return wc.getHTML( pars )

    def _getNavigationDrawer(self):
        #link = [{"url": urlHandlers.UHCategoryOverview.getURL(self._target), "title": _("Events overview")}]
        pars = {"target": self._target, "isModif": False}
        return wcomponents.WNavigationDrawer( pars, type = "Overview" )

class WCategoryMap(wcomponents.WTemplated):

    def __init__( self, categ ):
        self._categ = categ

    def getCategMap( self, categ ):
        res = []
        if len(categ.getSubCategoryList()) > 0:
            res.append("<ul>")
            for subcat in categ.getSubCategoryList():
                res.append("<li><a href='%s'>%s</a>"% (urlHandlers.UHCategoryDisplay.getURL(subcat), subcat.getName()))
                if subcat.hasAnyProtection():
                    res.append("""&nbsp;<span style="font-size: 0.8em; color: gray;">(%s)</span>"""% _("protected"))
                res.append(self.getCategMap(subcat))
            res.append("</ul>")
        return "".join(res)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars['categName'] =  self._categ.getName()
        vars["categDisplayURL"] = urlHandlers.UHCategoryDisplay.getURL(self._categ)
        vars['map'] = self.getCategMap(self._categ)
        return vars

class WPCategoryMap( WPCategoryDisplayBase ):

    def __init__( self, rh, categ ):
        WPCategoryDisplayBase.__init__( self, rh, categ )

    def _getTitle(self):
        return WPCategoryDisplayBase._getTitle(self) + " - " + _("Category Map")

    def _getBody( self, params ):
        wc = WCategoryMap( self._target )
        pars = {}
        return wc.getHTML( pars )

    def _getNavigationDrawer(self):
        #link = [{"url": urlHandlers.UHCategoryMap.getURL(self._target), "title": _("Category map")}]
        pars = {"target": self._target, "isModif": False}
        return wcomponents.WNavigationDrawer( pars, type = "Map" )


#---------------------------------------------------------------------------

class WConferenceCreation( wcomponents.WTemplated ):

    def __init__( self, targetCateg, type="conference", rh = None ):
        self._categ = targetCateg
        self._type = type
        self._rh = rh


    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        navigator = ""
        vars["title"] = vars.get("title","")
        vars["description"] = vars.get("description","")
        vars["keywords"] = vars.get("keywords","")
        vars["contactInfo"] = vars.get("contactInfo","")
        av=self._rh._getUser()
        tz=av.getTimezone()
        now = nowutc().astimezone(timezone(tz))
        vars["sDay"] = vars.get("sDay",now.day)
        vars["sMonth"] = vars.get("sMonth",now.month)
        vars["sYear"] = vars.get("sYear",now.year)
        vars["sHour"] = vars.get("sHour","8")
        vars["sMinute"] = vars.get("sMinute","00")
        vars["eDay"] = vars.get("eDay",now.day)
        vars["eMonth"] = vars.get("eMonth",now.month)
        vars["eYear"] = vars.get("eYear",now.year)
        vars["eHour"] = vars.get("eHour","18")
        vars["eMinute"] = vars.get("eMinute","00")

        vars["sDay_"] = {}
        vars["sMonth_"] = {}
        vars["sYear_"] = {}
        vars["sHour_"] = {}
        vars["sMinute_"] = {}
        vars["dur_"] = {}

        for i in range(0,10):
            vars["sDay_"][i] = vars.get("sDay_%s"%i,now.day)
            vars["sMonth_"][i] = vars.get("sMonth_%s"%i,now.month)
            vars["sYear_"][i] = vars.get("sYear_%s"%i,now.year)
            vars["sHour_"][i] = vars.get("sHour_%s"%i,"8")
            vars["sMinute_"][i] = vars.get("sMinute_%s"%i,"00")
            vars["dur_"][i] = vars.get("dur_%s"%i,"60")
        vars["nbDates"] = vars.get("nbDates",1)
        seltitle = Config.getInstance().getDefaultTimezone()
        if self._categ:
            seltitle= self._categ.getTimezone()
        vars["timezoneOptions"] = TimezoneRegistry.getShortSelectItemsHTML(seltitle)
        vars["locationName"] = vars.get("locationName","")
        vars["locationAddress"] = vars.get("locationAddress","")
        vars["roomName"] = vars.get("locationRoom","")
        #vars["locator"] = self._categ.getLocator().getWebForm()
        vars["protection"] = "public"
        vars["categ"] = {"id":"", "title":_("-- please, choose a category --")}
        if self._categ and not self._categ.hasSubcategories():
            if self._categ.isProtected() :
                vars["protection"] = "private"
            vars["categ"] = {"id":self._categ.getId(), "title":self._categ.getTitle()}
        vars["nocategs"] = False
        if not CategoryManager().getRoot().hasSubcategories():
            vars["nocategs"] = True
            rootcateg = CategoryManager().getRoot()
            if rootcateg.isProtected():
                vars["protection"] = "private"
            vars["categ"] = {"id":rootcateg.getId(), "title":rootcateg.getTitle()}
        #vars["event_type"] = ""
        vars["navigator"] = navigator
        vars["orgText"] = ""
        if vars.get("orgText","") != "":
            vars["orgText"] = vars.get("orgText","")
        elif self._rh._getUser():
            vars["orgText"] = self._rh._getUser().getStraightFullName()
        vars["chairText"] = vars.get("chairText","")
        vars["supportEmail"] = vars.get("supportEmail","")
        styles = theme_settings.get_themes_for(self._type)
        styleoptions = ""
        defStyle = ""
        if self._categ:
            defStyle = self._categ.getDefaultStyle(self._type)
        if defStyle == "":
            defStyle = theme_settings.defaults[self._type]
        for theme_id, theme_data in styles.viewitems():
            if theme_id == defStyle:
                selected = "selected"
            else:
                selected = ""
            styleoptions += "<option value=\"%s\" %s>%s</option>" % (theme_id, selected, theme_data['title'])
        vars["styleOptions"] = styleoptions

        vars["chairpersonDefined"] = vars.get("chairpersonDefined", [])

        vars["useRoomBookingModule"] = Config.getInstance().getIsRoomBookingActive()

        return vars

#---------------------------------------------------------------------------

class WPConferenceCreationMainData( WPCategoryDisplayBase ):

    _userData = ['favorite-user-list', 'favorite-user-ids']

    def getJSFiles(self):
        return WPCategoryDisplayBase.getJSFiles(self) + \
               self._includeJSPackage('Management')

    def _getHeader( self ):
        """
        """
        wc = wcomponents.WHeader( self._getAW() )
        return wc.getHTML( { "subArea": self._getSiteArea(), \
                             "loginURL": self._escapeChars(str(self.getLoginURL())),\
                             "logoutURL": self._escapeChars(str(self.getLogoutURL())) } )

    def _getNavigationDrawer(self):
        if self._target and self._target.isRoot():
            return
        else:
            pars = {"target": self._target, "isModif": False}
            return wcomponents.WNavigationDrawer( pars )

    def _getWComponent( self ):
        return WConferenceCreation( self._target, self._rh._event_type, self._rh )

    def _getBody( self, params ):
        ## TODO: TO REMOVE?????????
        #p = { "categDisplayURLGen": urlHandlers.UHCategoryDisplay.getURL }
        wc = self._getWComponent()
        params.update({"postURL": urlHandlers.UHConferencePerformCreation.getURL() })
        return "%s"%wc.getHTML( params )

class WPCategoryModifBase( WPCategoryBase ):

    _userData = ['favorite-user-ids']

    def getJSFiles(self):
        return (WPCategoryBase.getJSFiles(self) +
                main.WPMainBase.getJSFiles(self) +
                self._includeJSPackage('Management') +
                self._asset_env['modules_event_management_js'].urls())

    def getCSSFiles(self):
        return main.WPMainBase.getCSSFiles(self) + self._asset_env['event_management_sass'].urls()

    def _getHeader(self):
        wc = wcomponents.WHeader(self._getAW(), currentCategory=self._currentCategory())
        return wc.getHTML({
            'subArea': self._getSiteArea(),
            'loginURL': self._escapeChars(str(self.getLoginURL())),
            'logoutURL': self._escapeChars(str(self.getLogoutURL()))
        })

    def _getNavigationDrawer(self):
        pars = {"target": self._target , "isModif" : True}
        return wcomponents.WNavigationDrawer( pars, bgColor = "white" )

    def _createTabCtrl( self ):
        pass

    def _setActiveTab( self ):
        pass

    def _getBody(self, params):
        self._createTabCtrl()
        self._setActiveTab()

        frame = WCategoryModifFrame()

        return frame.getHTML({
            "category": self._target,
            "body": self._getPageContent(params),
            "sideMenu": render_sidemenu('category-management-sidemenu-old', active_item=self.sidemenu_option,
                                        category=self._target, old_style=True)
        })

    def _getTabContent( self, params ):
        return "nothing"

    def _getPageContent( self, params ):
        return "nothing"

    def _getSiteArea(self):
        return "ModificationArea"


class WCategoryModifFrame(wcomponents.WTemplated):

    def __init__( self ):
        pass

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        return vars

class WPCategModifMain( WPCategoryModifBase ):
    sidemenu_option = 'general'


class WCategModifMain(wcomponents.WTemplated):

    def __init__( self, category ):
        self._categ = category

    def __getSubCategoryItems( self, sl, modifURLGen ):
        temp = []
        for categ in sl:
            id = categ.getId()
            selbox = """<select name="newpos%s" onChange="this.form.oldpos.value='%s';this.form.submit();">""" % (sl.index(categ),sl.index(categ))
            for i in range (1,len(sl)+1):
                if i==sl.index(categ)+1:
                    selbox += "<option selected value='%s'>%s" % (i-1,i)
                else:
                    selbox += "<option value='%s'>%s" % (i-1,i)
            selbox += """
                </select>"""
            temp.append("""
                <tr>
                    <td width="3%%">
                        <input type="checkbox" name="selectedCateg" value="%s">
                    </td>
                    <td>%s</td>
                    <td style="padding-left:10px;">
                        <a href="%s">%s</a>
                    </td>
                </tr>"""%(id, selbox,modifURLGen( categ ), categ.getName().strip() or "[no title]"))
        html = i18nformat("""
                <input type="hidden" name="oldpos">
                <table align="left" width="100%%">
                <tr>
                    <td width="3%%" nowrap><img src="%s" border="0" alt="Select all" onclick="javascript:selectAll(document.contentForm.selectedCateg)"><img src="%s" border="0" alt="Deselect all" onclick="javascript:deselectAll(document.contentForm.selectedCateg)"></td>
                    <td></td>
                    <td class="titleCellFormat" width="100%%" style="padding-left:10px;"> _("Category name")</td>
                </tr>
                %s
                </table>""")%(Config.getInstance().getSystemIconURL("checkAll"), Config.getInstance().getSystemIconURL("uncheckAll"), "".join( temp ))
        return html

    def __getConferenceItems(self, cl, modifURLGen):
        temp = []
        cl = list(cl)
        preload_events(cl)
        for conf in cl:
            temp.append("""
                <tr>
                    <td width="3%%">
                        <input type="checkbox" name="selectedConf" value="%s">
                    </td>
                    <td align="center" width="17%%">%s</td>
                    <td align="center" width="17%%">%s</td>
                    <td width="100%%"><a href="%s">%s</a></td>
                </tr>"""%(conf.getId(), conf.getAdjustedStartDate().date(), conf.getAdjustedEndDate().date(),modifURLGen(conf), conf.getTitle()))
        html = i18nformat("""<table align="left" width="100%%">
                <tr>
                    <td width="3%%" nowrap><img src="%s" border="0" alt="Select all" onclick="javascript:selectAll(document.contentForm.selectedConf)"><img src="%s" border="0" alt="Deselect all" onclick="javascript:deselectAll(document.contentForm.selectedConf)"></td>
                    <td align="center" width="17%%" class="titleCellFormat" style="border-right:5px solid #FFFFFF; border-bottom: 1px solid #FFFFFF;"> _("Start date")</td>
                    <td align="center" width="17%%" class="titleCellFormat" style="border-right:5px solid #FFFFFF; border-bottom: 1px solid #FFFFFF;"> _("End date")</td>
                    <td width="100%%" class="titleCellFormat" style="border-right:5px solid #FFFFFF; border-bottom: 1px solid #FFFFFF;"> _("Conference title")</td>
                </tr>
        %s</table>""")%(Config.getInstance().getSystemIconURL("checkAll"), Config.getInstance().getSystemIconURL("uncheckAll"), "".join( temp ))
        return html

    def getVars( self ):

        index = Catalog.getIdx('categ_conf_sd').getCategory(self._categ.getId())
        vars = wcomponents.WTemplated.getVars( self )
        vars["locator"] = self._categ.getLocator().getWebForm()
        vars["name"] = self._categ.getName()

        vars["description"] = self._categ.getDescription()

        if self._categ.getIcon() is not None:
            vars["icon"] = """<img src="%s" width="16" height="16" alt="category">"""%urlHandlers.UHCategoryIcon.getURL( self._categ)
        else:
            vars["icon"] = "None"
        vars["dataModifButton"] = ""
        if not self._categ.isRoot():
            vars["dataModifButton"] = i18nformat("""<input type="submit" class="btn" value="_("modify")">""")
        vars["removeItemsURL"] = vars["actionSubCategsURL"]
        if not self._categ.getSubCategoryList():
            vars['containsEvents'] = True
            vars["removeItemsURL"] = vars["actionConferencesURL"]
            vars["items"] = self.__getConferenceItems(index.itervalues(), vars["confModifyURLGen"])
        else:
            vars['containsEvents'] = False
            vars["items"] = self.__getSubCategoryItems( self._categ.getSubCategoryList(), vars["categModifyURLGen"] )
        vars["defaultMeetingStyle"] = theme_settings.themes[theme_settings.defaults['meeting']]['title']
        vars["defaultLectureStyle"] = theme_settings.themes[theme_settings.defaults['simple_event']]['title']

##        vars["defaultVisibility"] = self._categ.getVisibility()
        vars["defaultTimezone"] = self._categ.getTimezone()
        visibility = self._categ.getVisibility()
        categpath = self._categ.getCategoryPath()
        categpath.reverse()
        if visibility > len(categpath):
            vars["defaultVisibility"] = _("Everywhere")
        elif visibility == 0:
            vars["defaultVisibility"] = _("Nowhere")
        else:
            categId = categpath[visibility-1]
            cat = conference.CategoryManager().getById(categId)
            vars["defaultVisibility"] = cat.getName()

        return vars


class WPCategoryModification( WPCategModifMain ):

    def _getPageContent( self, params ):
        wc = WCategModifMain( self._target )
        pars = { \
"dataModificationURL": urlHandlers.UHCategoryDataModif.getURL( self._target ), \
"addSubCategoryURL": urlHandlers.UHCategoryCreation.getURL(self._target),
"addConferenceURL": urlHandlers.UHConferenceCreation.getURL( self._target ), \
"confModifyURLGen": urlHandlers.UHConferenceModification.getURL, \
"categModifyURLGen": urlHandlers.UHCategoryModification.getURL, \
"actionSubCategsURL": urlHandlers.UHCategoryActionSubCategs.getURL(self._target),
"actionConferencesURL": urlHandlers.UHCategoryActionConferences.getURL(self._target)}
        return wc.getHTML( pars )


class WCategoryDataModification(wcomponents.WTemplated):

    def __init__( self, category ):
        self._categ = category

    def _getVisibilityHTML(self):
        visibility = self._categ.getVisibility()
        topcat = self._categ
        level = 0
        selected = ""
        if visibility == 0:
            selected = "selected"
        vis = [ i18nformat("""<option value="0" %s> _("Nowhere")</option>""") % selected]
        while topcat:
            level += 1
            selected = ""
            if level == visibility:
                selected = "selected"
            if topcat.getId() != "0":
                vis.append("""<option value="%s" %s>%s</option>""" % (level, selected, truncateTitle(topcat.getName(), 70)))
            topcat = topcat.getOwner()
        selected = ""
        if visibility > level:
            selected = "selected"
        vis.append( i18nformat("""<option value="999" %s> _("Everywhere")</option>""") % selected)
        vis.reverse()
        return "".join(vis)

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["name"] = self._categ.getName()
        vars["description"] = self._categ.getDescription()
        vars["visibility"] = self._getVisibilityHTML()
        vars["timezoneOptions"] = TimezoneRegistry.getShortSelectItemsHTML(self._categ.getTimezone())
        if self._categ.getIcon() is not None:
            vars["icon"] = """<img src="%s" width="16" height="16" alt="category">"""%urlHandlers.UHCategoryIcon.getURL( self._categ)
        else:
            vars["icon"] = "None"
        for evt_type in ("simple_event", "meeting"):
            themes = theme_settings.get_themes_for(evt_type)
            styleoptions = ""
            for theme_id, theme_data in themes.viewitems():
                defStyle = self._categ.getDefaultStyle(evt_type)
                if defStyle == "":
                    defStyle = theme_settings.defaults[evt_type]
                if theme_id == defStyle:
                    selected = "selected"
                else:
                    selected = ""
                styleoptions += "<option value=\"%s\" %s>%s</option>" % (theme_id, selected,
                                                                         theme_data['title'])
            vars["%sStyleOptions" % evt_type] = styleoptions

        return vars


class WPCategoryDataModification(WPCategModifMain):

    def _getPageContent(self, params):
        wc = WCategoryDataModification(self._target)
        pars = {"postURL": urlHandlers.UHCategoryPerformModification.getURL(self._target)}
        return wc.getHTML(pars)


class WCategoryCreation(wcomponents.WTemplated):

    def __init__(self, target):
        self.__target = target

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["locator"] = self.__target.getLocator().getWebForm()

        for evt_type in ("simple_event", "meeting"):
            styleoptions = ""

            for theme_id, theme_data in theme_settings.get_themes_for(evt_type).viewitems():
                defStyle = self.__target.getDefaultStyle(evt_type)

                if defStyle == "":
                    defStyle = theme_settings.defaults[evt_type]
                if theme_id == defStyle:
                    selected = "selected"
                else:
                    selected = ""

                styleoptions += "<option value=\"%s\" %s>%s</option>" % (theme_id, selected, theme_data['title'])
            vars[evt_type + "StyleOptions"] = styleoptions

        default_tz = Config.getInstance().getDefaultTimezone()
        vars["timezoneOptions"] = TimezoneRegistry.getShortSelectItemsHTML(default_tz)
        vars["categTitle"] = self.__target.getTitle()
        if self.__target.isProtected():
            vars["categProtection"] = "private"
        else:
            vars["categProtection"] = "public"
        vars["numConferences"] = len(self.__target.conferences)

        return vars


class WPCategoryCreation(WPCategModifMain):

    def _getPageContent(self, params):
        wc = WCategoryCreation(self._target)
        pars = {"categDisplayURLGen": urlHandlers.UHCategoryDisplay.getURL, \
                "postURL": urlHandlers.UHCategoryPerformCreation.getURL(self._target)}
        return wc.getHTML(pars)


class WCategoryDeletion(object):

    def __init__(self, categoryList):
        self._categList = categoryList

    def getHTML(self, actionURL):
        categories = []

        for categ in self._categList:
            categories.append("""<li><i>%s</i></li>""" % categ.getName())

        msg = {'challenge': _("Are you sure that you want to delete the following categories?"),
               'target': "".join(categories),
               'important': True,
               'subtext': _("Note that all the existing sub-categories below will also be deleted")
               }

        wc = wcomponents.WConfirmation()
        categIdList = []

        for categ in self._categList:
            categIdList.append(categ.getId())

        return wc.getHTML(msg, actionURL, {"selectedCateg": categIdList},
                          confirmButtonCaption=_("Yes"),
                          cancelButtonCaption=_("No"),
                          severity='danger')


class WConferenceDeletion(wcomponents.WTemplated):
    pass


class WPSubCategoryDeletion(WPCategModifMain):

    def _getPageContent(self, params):
        selCategs = params["subCategs"]
        wc = WCategoryDeletion(selCategs)
        return wc.getHTML(urlHandlers.UHCategoryActionSubCategs.getURL(self._target))


class WPConferenceDeletion(WPCategModifMain):

    def _getPageContent(self, params):
        wc = WConferenceDeletion()
        return wc.getHTML({'eventList': params["events"],
                           'postURL': urlHandlers.UHCategoryActionConferences.getURL(self._target),
                           'cancelButtonCaption': _("No"),
                           'confirmButtonCaption': _("Yes")})


class WItemReallocation(wcomponents.WTemplated):

    def __init__(self, itemList):
        self._itemList = itemList

    def getHTML(self, selectTree, params):
        self._sTree = selectTree
        return wcomponents.WTemplated.getHTML(self, params)

    def _getItemDescription(self, item):
        return ""

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )
        l = []
        for item in self._itemList:
            l.append("<li><b>%s</b>"%self._getItemDescription(item))
        vars["selectedItems"] = "".join(l)
        vars["categTree"] = self._sTree.getHTML()
        return vars


class WCategoryReallocation( WItemReallocation ):

    def _getItemDescription( self, item ):
        return item.getName()


class WConferenceReallocation( WItemReallocation ):

    def _getItemDescription( self, item ):
        return item.getTitle()


class CategSelectTree:

    def __init__( self, aw, excludedCat, expandedCat, \
                        selectURLGen, expandURLGen, movingConference = 0 ):
        self._aw = aw
        self._excludedCategs = excludedCat
        self._expandedCategs = expandedCat
        self._selectURLGen = selectURLGen
        self._expandURLGen = expandURLGen
        self._movingConference = movingConference

    def _getItem( self, categ, level=0 ):
        if not categ.canAccess( self._aw ):
            return ""
        html = ""
        for i in range(level):
            html = "%s&nbsp;&nbsp;&nbsp;"%html
        cfg = Config.getInstance()
        if categ in self._excludedCategs:
            return """%s<img src="%s" border="0" alt=""> %s"""%(html, cfg.getSystemIconURL("collapsd.png"), categ.getName())
        if (self._movingConference) and categ.getSubCategoryList():
            title = """%s"""%categ.getName()
        else:
            title = """<a href="%s">%s</a>"""%(self._selectURLGen( categ ), \
                                                categ.getName())
        if categ in self._expandedCategs:
            ex = copy( self._expandedCategs )
            ex.remove( categ )
            html = """%s<a href="%s"><img src="%s" border="0" alt=""></a> %s"""%(html, self._expandURLGen( ex ), cfg.getSystemIconURL("exploded.png"), title)
            for subcat in categ.getSubCategoryList():
                html = "%s<br>%s"%(html, self._getItem(subcat, level+1) )
        else:
            html = """%s<a href="%s"><img src="%s" border="0" alt=""></a> %s"""%(html, self._expandURLGen( self._expandedCategs+[categ] ), cfg.getSystemIconURL("collapsd.png"), title)
        return html

    def getHTML( self ):
        cm = conference.CategoryManager()
        return self._getItem( cm.getRoot() )


class WPCategoryReallocation( WPCategModifMain ):

    def _getReAllocateCategsURL( self, destination ):
        url = urlHandlers.UHCategoryActionSubCategs.getURL( destination )
        selectedCategs = []
        for c in self._categs:
            selectedCategs.append( c.getId() )
        url.addParam( "selectedCateg", selectedCategs )
        url.addParam( "confirm", "" )
        url.addParam( "reallocate", "" )
        return url

    def _getCategExpandCategURL( self, expandedCategs ):
        selected = []
        for c in self._categs:
            selected.append( c.getId() )
        expanded = []
        for c in expandedCategs:
            expanded.append( c.getId() )
        url = urlHandlers.UHCategoryActionSubCategs.getURL( self._target )
        url.addParam( "selectedCateg", selected )
        url.addParam( "ex", expanded )
        url.addParam( "reallocate", "" )
        return url

    def _getExpandedCategs( self, params ):
        exIdList = params.get("ex", [])
        if not isinstance( exIdList, list ):
            exIdList = [ exIdList ]
        expanded = []
        cm = conference.CategoryManager()
        for categId in exIdList:
            expanded.append( cm.getById( categId ) )
        return expanded

    def _getPageContent( self, params ):
        self._categs = params["subCategs"]
        expanded = self._getExpandedCategs( params )
        pars = {"cancelURL": urlHandlers.UHCategoryModification.getURL( self._target ) }
        tree = CategSelectTree( self._getAW(), self._categs, \
                                            expanded, \
                                            self._getReAllocateCategsURL, \
                                            self._getCategExpandCategURL )
        wc = WCategoryReallocation( self._categs )
        return wc.getHTML( tree, pars )


class WPConferenceReallocation( WPCategModifMain ):

    def _getReAllocateConfsURL( self, destination ):
        url = urlHandlers.UHCategoryActionConferences.getURL( destination )
        url.addParam( "srcCategId", self._target.getId() )
        url.addParam( "selectedConf", self._confIds)
        url.addParam( "confirm", "" )
        url.addParam( "reallocate", "" )
        return url

    def _getExpandCategURL( self, expandedCategs ):
        expanded = []
        for c in expandedCategs:
            expanded.append( c.getId() )
        url = urlHandlers.UHCategoryActionConferences.getURL( self._target )
        url.addParam( "ex", expanded )
        url.addParam( "reallocate", "" )
        url.addParam( "selectedConf", self._confIds )
        return url

    def _getExpandedCategs( self, params ):
        exIdList = params.get("ex", [])
        if not isinstance( exIdList, list ):
            exIdList = [ exIdList ]
        expanded = []
        cm = conference.CategoryManager()
        for categId in exIdList:
            expanded.append( cm.getById( categId ) )
        return expanded

    def _getPageContent( self, params ):
        self._confs = params["confs"]
        self._confIds = []
        for c in self._confs:
            self._confIds.append( c.getId() )
        expanded = self._getExpandedCategs( params )
        pars = {"cancelURL": urlHandlers.UHCategoryModification.getURL( self._target ) }
        tree = CategSelectTree( self._getAW(), [], \
                                            expanded, \
                                            self._getReAllocateConfsURL, \
                                            self._getExpandCategURL, 1 )
        wc = WConferenceReallocation( self._confs )
        return wc.getHTML( tree, pars )


class WCategModifAC(wcomponents.WTemplated):

    def __init__( self, category ):
        self._categ = category

    def _getControlUserList(self):
        result = fossilize(self._categ.getManagerList())
        # get pending users
        for email in self._categ.getAccessController().getModificationEmail():
            pendingUser = {}
            pendingUser["email"] = email
            pendingUser["pending"] = True
            result.append(pendingUser)
        return result

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )

        vars["modifyControlFrame"] = wcomponents.WModificationControlFrame().getHTML(self._categ)
        if self._categ.isRoot() :
            type = 'Home'
        else :
            type = 'Category'

        vars["accessControlFrame"] = wcomponents.WAccessControlFrame().getHTML(\
                                                    self._categ,\
                                                    vars["setVisibilityURL"],\
                                                    type)
        if not self._categ.isProtected():
            df =  wcomponents.WDomainControlFrame( self._categ )
            vars["accessControlFrame"] += "<br>%s"%df.getHTML()
        vars["confCreationControlFrame"] = ""
        vars["categoryId"] = self._categ.getId()
        if not self._categ.getSubCategoryList():
            frame = wcomponents.WConfCreationControlFrame( self._categ )
            p = { "setStatusURL": vars["setConferenceCreationControlURL"] }
            vars["confCreationControlFrame"] = frame.getHTML(p)
        vars["managers"] = self._getControlUserList()
        return vars

class WPCategModifAC( WPCategoryModifBase ):
    sidemenu_option = 'protection'

    def _getPageContent(self, params):
        wc = WCategModifAC(self._target)
        pars = {
            "setVisibilityURL": urlHandlers.UHCategorySetVisibility.getURL(self._target),
            "setConferenceCreationControlURL": urlHandlers.UHCategorySetConfCreationControl.getURL(self._target)
        }
        return wc.getHTML(pars)

#---------------------------------------------------------------------------------

class WCategModifTools(wcomponents.WTemplated):

    def __init__( self, category ):
        self._categ = category

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["deleteButton"] = ""
        vars["id"] = self._categ.getId()
        if not self._categ.isRoot():
            vars["deleteButton"] = i18nformat("""<input type="submit" class="btn" value="_("delete this category")">""")
        return vars


class WPCategModifTools( WPCategoryModifBase ):
    sidemenu_option = 'tools'

    def _getPageContent( self, params ):
        wc = WCategModifTools( self._target )
        pars = { \
"deleteCategoryURL": urlHandlers.UHCategoryDeletion.getURL(self._target) }
        return wc.getHTML( pars )


class WPCategoryDeletion( WPCategModifTools ):

    def _getPageContent( self, params ):
        wc = WCategoryDeletion( [self._target] )
        return wc.getHTML( urlHandlers.UHCategoryDeletion.getURL( self._target ) )
