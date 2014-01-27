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

from xml.sax.saxutils import quoteattr, escape
from datetime import datetime,timedelta

import MaKaC.webinterface.wcomponents as wcomponents
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.materialFactories as materialFactories
import MaKaC.webinterface.navigation as navigation
import MaKaC.schedule as schedule
import MaKaC.conference as conference
import MaKaC.webinterface.linking as linking
from MaKaC.webinterface.pages.conferences import WPConferenceBase, WPConfModifScheduleGraphic, \
    WPConferenceDefaultDisplayBase, WContribParticipantList, WPConferenceModifBase
from MaKaC.webinterface.pages.metadata import WICalExportBase
from MaKaC.common import info
import MaKaC.webinterface.timetable as timetable
from MaKaC.webinterface.common.contribStatusWrapper import ContribStatusList
import MaKaC.common.filters as filters
import MaKaC.webinterface.common.contribFilters as contribFilters
from MaKaC.webinterface.common.person_titles import TitlesRegistry
from MaKaC.common.utils import isStringHTML
from MaKaC import user
from MaKaC.i18n import _
from indico.util.i18n import i18nformat

from pytz import timezone
from MaKaC.common.timezoneUtils import DisplayTZ
from indico.util import json
from indico.util.date_time import format_date, format_datetime
import pytz
import MaKaC.common.timezoneUtils as timezoneUtils
from MaKaC.common.fossilize import fossilize
from MaKaC.fossils.conference import IConferenceEventInfoFossil, ISessionFossil
from MaKaC.user import Avatar
from MaKaC.common.TemplateExec import render

from indico.core.config import Config


class WPSessionBase(WPConferenceBase):

    def __init__(self, rh, session):
        self._session = session
        WPConferenceBase.__init__(self, rh, self._session.getConference())


class WPSessionDisplayBase(WPSessionBase):
    pass


class WPSessionDefaultDisplayBase(WPConferenceDefaultDisplayBase, WPSessionDisplayBase):

    def __init__(self, rh, session):
        WPSessionDisplayBase.__init__(self, rh, session)


class WContributionListDisplayTab(wcomponents.WTemplated):

    def __init__(self, aw, session, tab=None):
        self._aw = aw
        self._session = session
        self._activeTab = tab

    def _getURL(self, sortByField):
        url = urlHandlers.UHSessionDisplay.getURL(self._session)

        if self._activeTab:
            url.addParam("tab", self._activeTab)

        return url

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars['contributions'] = self._session.getContributionList()
        vars['accessWrapper'] = self._aw
        vars['posterSession'] = (self._session.getScheduleType() == "poster")
        return vars


class _NoWitdhdrawFF(filters.FilterField):
    _id = "no_withdrawn"

    def __init__(self):
        pass

    def satisfies(self, contrib):
        return not isinstance(contrib.getCurrentStatus(), conference.ContribStatusWithdrawn)


class _NoWithdrawnFilterCriteria(filters.FilterCriteria):

    def __init__(self, conf):
        self._fields = {"no_withdrawn": _NoWitdhdrawFF()}


class WSessionDisplayBase(WICalExportBase):

    def __init__(self,aw,session):
        self._aw = aw
        self._session = session
        self._tz = timezoneUtils.DisplayTZ(self._aw,self._session.getConference()).getDisplayTZ()

    def _getResourceName(self, resource):
        if isinstance(resource, conference.Link):
            return resource.getName() if resource.getName() != "" and resource.getName() != resource.getURL() else resource.getURL()
        else:
            return resource.getName() if resource.getName() != "" and resource.getName() != resource.getFileName() else resource.getFileName()

    def getVars(self):
        vars = wcomponents.WTemplated.getVars( self )

        slotConveners = []
        for entry in self._session.getSchedule().getEntries():
            slot = entry.getOwner()
            conveners = []
            for convener in slot.getOwnConvenerList():
                conveners.append({'fullName': convener.getFullName(), 'email': convener.getEmail() if self._aw.getUser() else "", 'affiliation' : convener.getAffiliation()})
            if conveners:
                slotConveners.append({'title': slot.getTitle(), 'startDate': slot.getAdjustedStartDate(self._tz), 'endDate': slot.getAdjustedEndDate(self._tz), 'conveners': conveners})
        vars["slotConveners"] = slotConveners

        eventInfo = fossilize(self._session.getConference(), IConferenceEventInfoFossil, tz = self._tz)
        eventInfo['timetableSession'] = fossilize(self._session, ISessionFossil, tz = self._tz)
        vars["ttdata"]= schedule.ScheduleToJson.process(self._session.getSchedule(), self._tz, None, days = None, mgmtMode = False)
        vars["eventInfo"]= eventInfo

        vars["getResourceName"] = lambda resource: self._getResourceName(resource)
        vars["session"] = vars["target"] = self._session
        vars["urlICSFile"] = urlHandlers.UHSessionToiCal.getURL(self._session)
        vars.update(self._getIcalExportParams(self._aw.getUser(), '/export/event/%s/session/%s.ics' % \
                                              (self._session.getConference().getId(), self._session.getId())))
        vars["conf"] = self._session.getConference()
        vars["contributions"] = sorted(self._session.getContributionList(), key=lambda contrib: contrib.getTitle())
        return vars


# TODO: These classes are actually the same, no?  (Pedro)

class WSessionDisplayFull(WSessionDisplayBase):
    pass


class WSessionDisplayMin(WSessionDisplayBase):
    pass


class WSessionDisplay:

    def __init__(self, aw, session):
        self._aw = aw
        self._session = session

    def getHTML(self):
        c = WSessionDisplayFull(self._aw, self._session)
        return c.getHTML()


class WPSessionDisplay( WPSessionDefaultDisplayBase ):
    navigationEntry = navigation.NESessionDisplay

    def _getBody(self, params):
        wc = WSessionDisplay(self._getAW(), self._session)
        return wc.getHTML()

    def getJSFiles(self):
        return WPSessionDefaultDisplayBase.getJSFiles(self) + \
               self._includeJSPackage('MaterialEditor') + \
               self._includeJSPackage('Timetable')

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

        banner = wcomponents.WTimetableBannerModif(self._getAW(), self._session).getHTML()
        body = wcomponents.WTabControl(self._tabCtrl, self._getAW()).getHTML(self._getTabContent(params))
        return banner + body

    def getJSFiles(self):
        return WPConferenceModifBase.getJSFiles(self) + \
            self._asset_env['contributions_js'].urls()

    def getCSSFiles(self):
        return WPConferenceModifBase.getCSSFiles(self) + \
            self._asset_env['contributions_sass'].urls()

    def _getHeadContent(self):
        return WPConferenceModifBase._getHeadContent(self) + render('js/mathjax.config.js.tpl') + \
            '\n'.join(['<script src="{0}" type="text/javascript"></script>'.format(url)
                       for url in self._asset_env['mathjax_js'].urls()])


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

    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )

        vars["dataModificationURL"]=quoteattr(str(urlHandlers.UHSessionDataModification.getURL(self._session)))
        vars["code"]=self.htmlText(self._session.getCode())
        vars["title"]=self._session.getTitle()
        if isStringHTML(self._session.getDescription()):
            vars["description"] = self._session.getDescription()
        else:
            vars["description"] = """<table class="tablepre"><tr><td><pre>%s</pre></td></tr></table>""" % self._session.getDescription()
        vars["bgcolor"] = self._session.getColor()
        vars["textcolor"] = self._session.getTextColor()
        vars["entryDuration"]=self.htmlText((datetime(1900,1,1)+self._session.getContribDuration()).strftime("%Hh%M'"))
        vars["tt_type"]=self.htmlText(self._session.getScheduleType())
        type = self._session.getConference().getType()
        if type == "conference":
            vars["Type"]=WSessionModifMainType().getHTML(vars)
            vars["Colors"]=WSessionModifMainColors().getHTML(vars)
            vars["Code"]=WSessionModifMainCode().getHTML(vars)
            vars["Rowspan"]=6
        else:
            vars["Type"]=""
            vars["Colors"]=""
            vars["Code"]=""
            vars["Rowspan"]=4
        vars["confId"] = self._session.getConference().getId()
        vars["sessionId"] = self._session.getId()
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
        message = _("The session is currently locked and you cannot modify it in this status. ")
        if self._session.getConference().canModify(self._rh.getAW()):
            message += _("If you unlock the session, you will be able to modify its details again.")
        return wcomponents.WClosed().getHTML({"message": message,
                                             "postURL": urlHandlers.UHSessionOpen.getURL(self._session),
                                             "showUnlockButton": self._session.getConference().canModify(self._rh.getAW()),
                                             "unlockButtonCaption": _("Unlock session")})

#------------------------------------------------------------------------------------

class WPSessionDataModification(WPSessionModification):

    def _getTabContent(self,params):
        title="Edit session data"
        p=wcomponents.WSessionModEditData(self._session.getConference(),self._getAW(),title)
        params["postURL"]=urlHandlers.UHSessionDataModification.getURL(self._session)
        params["colorChartIcon"]=Config.getInstance().getSystemIconURL("colorchart")
        params["bgcolor"] = self._session.getColor()
        params["textcolor"] = self._session.getTextColor()
        params["textColorToLinks"]=""
        if self._session.isTextColorToLinks():
            params["textColorToLinks"]="checked=\"checked\""

        params["convener"] = ""
        return p.getHTML(params)

#---------------------------------------------------------------------------

class WPModEditDataConfirmation(WPSessionModification):

    def _getTabContent(self,params):
        wc = wcomponents.WConfirmation()

        msg = {
            'challenge': _("Are you sure you want to change the schedule of this session from '{0}' to '{1}'?").format(
                self._session.getScheduleType(), params["tt_type"]),
            'target': self._session.getTitle(),
            'subtext': _("Note that if you continue any contribution scheduled within any slot of the current session will be unscheduled")
            }

        url=urlHandlers.UHSessionDataModification.getURL(self._session)
        return wc.getHTML(msg,url,params)


class WPSessionModifSchedule( WPSessionModifBase, WPConfModifScheduleGraphic  ):

    _userData = ['favorite-user-list']

    def __init__( self, rh, session):
        WPSessionModifBase.__init__(self, rh, session)
        WPConfModifScheduleGraphic.__init__( self, rh, session.getConference() )
        self._session = session

    def _setActiveTab(self):
        self._tabTimetable.setActive()

    def getJSFiles(self):
        return WPConfModifScheduleGraphic.getJSFiles(self)

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
        return WSessionModifSchedule(self._session)

    def _getTabContent( self, params ):
        return self._getTTPage(params)

class WSessionModifSchedule(wcomponents.WTemplated):

    def __init__(self, session, **params):
        wcomponents.WTemplated.__init__(self, **params)
        self._session = session

    def getVars( self ):
        vars=wcomponents.WTemplated.getVars(self)
        tz = self._session.getTimezone()
        vars["timezone"]= tz

        vars['ttdata'] = json.dumps(schedule.ScheduleToJson.process(self._session.getSchedule(), tz,
                                                                           None, days = None, mgmtMode = True))

        eventInfo = fossilize(self._session.getConference(), IConferenceEventInfoFossil, tz=tz)
        eventInfo['timetableSession'] = fossilize(self._session, ISessionFossil, tz=tz)
        eventInfo['isCFAEnabled'] = self._session.getConference().getAbstractMgr().isActive()
        vars['eventInfo'] = json.dumps(eventInfo)

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


class WSessionModifAC(wcomponents.WTemplated):

    def __init__(self,session):
        self._session=session

    def _getSessionChairList(self, rol):
        # get the lists we need to iterate
        if rol == "manager":
            list = self._session.getManagerList()
            pendingList = self._session.getAccessController().getModificationEmail()
        elif rol == "coordinator":
            list = self._session.getCoordinatorList()
            pendingList = self._session.getConference().getPendingQueuesMgr().getPendingCoordinatorsKeys()
        result = []
        for sessionChair in list:
            sessionChairFossil = fossilize(sessionChair)
            if isinstance(sessionChair, Avatar):
                isConvener = False
                if self._session.hasConvenerByEmail(sessionChair.getEmail()):
                    isConvener = True
                sessionChairFossil['isConvener'] = isConvener
            result.append(sessionChairFossil)
        # get pending users
        for email in pendingList:
            pendingUser = {}
            pendingUser["email"] = email
            pendingUser["pending"] = True
            result.append(pendingUser)
        return result

    def getVars(self):
        vars=wcomponents.WTemplated.getVars(self)
        wc=wcomponents.WAccessControlFrame()
        vars["accessControlFrame"] = wc.getHTML(self._session, urlHandlers.UHSessionSetVisibility.getURL(self._session),
                                                "Session")
        if not self._session.isProtected():
            df=wcomponents.WDomainControlFrame(self._session)
            vars["accessControlFrame"] += "<br>%s"%df.getHTML()
        wc=wcomponents.WModificationControlFrame()
        vars["modifyControlFrame"] = wc.getHTML(self._session)

        vars["confId"] = self._session.getConference().getId()
        vars["sessionId"] = self._session.getId()
        vars["managers"] = self._getSessionChairList("manager")
        vars["coordinators"] = self._getSessionChairList("coordinator")
        return vars


class WPSessionModifAC( WPSessionModifBase ):

    def _setActiveTab( self ):
        self._tabAC.setActive()

    def _getTabContent( self, params ):
        comp=WSessionModifAC(self._session)
        return comp.getHTML()

class WSessionModifTools(wcomponents.WTemplated):
    pass


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
        return WSessionModifTools().getHTML( { "deleteSessionURL": urlHandlers.UHSessionDeletion.getURL(self._session),
                                              "lockSessionURL": urlHandlers.UHSessionClose.getURL(self._session)} )

class WPSessionClosing(WPSessionModifTools):

    def _getTabContent(self, params):
        msg = {'challenge': _("Are you sure that you want to lock this session?"),
               'target': self._session.getTitle(),
               'subtext': _("Note that if you lock this session, you will not be able to change its details any more. "
                "Only the creator of the event or an administrator of the system / category can unlock a session."),
               }

        wc = wcomponents.WConfirmation()
        return wc.getHTML(msg,
                          urlHandlers.UHSessionClose.getURL(self._session),
                          {},
                          severity="warning",
                          confirmButtonCaption=_("Yes, lock this session"),
                          cancelButtonCaption=_("No"))

class WPSessionDeletion( WPSessionModifTools ):

    def _getTabContent( self, params ):

        msg = {
            'challenge': _("Are you sure that you want to delete this session?"),
            'target': self._session.getTitle(),
            'subtext': _("Note that if you delete this session all the items under it will also be deleted")
            }

        wc = wcomponents.WConfirmation()
        return wc.getHTML(msg,
                          urlHandlers.UHSessionDeletion.getURL( self._session ),
                          {},
                          severity="danger",
                          confirmButtonCaption= _("Yes"), cancelButtonCaption= _("No"))

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
        res=[ i18nformat("""<input type="checkbox" name="typeShowNoValue" value="--none--"%s>--_("not specified")--""")%checked]
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
        res=[ i18nformat("""<input type="checkbox" name="trackShowNoValue" value="--none--"%s>--_("not specified")--""")%checked]
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
                        ("--other--", _("other")),("--none--", i18nformat("""--_("no material")--"""))]:
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
            vars["authSearch"]=quoteattr(str(authField.getValues()[0]))
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
            vars["startDate"]= i18nformat("""--_("not scheduled")--""")
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
        res=[ i18nformat("""<option value="--none--">--_("none")--</option>""")]
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

    _userData = ['favorite-user-list']

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


class WSessionICalExport(WICalExportBase):

    def __init__(self, session, user):
        self._session = session
        self._user = user

    def getVars(self):
        vars = wcomponents.WTemplated.getVars(self)
        vars["target"] = vars["session"] = vars["item"] = self._session
        vars["urlICSFile"] =  urlHandlers.UHSessionToiCal.getURL(self._session)

        vars.update(self._getIcalExportParams(self._user, '/export/event/%s/session/%s.ics' % \
                                              (self._session.getConference().getId(), self._session.getId())))
        return vars
