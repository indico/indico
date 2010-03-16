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

from datetime import datetime
from pytz import timezone
from MaKaC.plugins.base import PluginsHolder

from MaKaC.user import Avatar
from MaKaC.user import CERNGroup

try:
    import libxml2
    import libxslt
except ImportError:
    pass
import string,re
import simplejson

import MaKaC.conference as conference
import MaKaC.schedule as schedule
import MaKaC.webcast as webcast
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.displayMgr as displayMgr
from MaKaC.common.general import DEVELOPMENT
from MaKaC.webinterface.linking import RoomLinker
from Configuration import Config
from xmlGen import XMLGen
import os, time
from MaKaC.i18n import _
from MaKaC.common.timezoneUtils import DisplayTZ, nowutc
from MaKaC.common.utils import getHierarchicalId, resolveHierarchicalId
from MaKaC.common.cache import MultiLevelCache, MultiLevelCacheEntry
from MaKaC.rb_location import CrossLocationQueries, CrossLocationDB


def fake(string1=""):
    return ""

# TODO This really needs to be fixed... no i18n and strange implementation using month names as keys
def stringToDate( str ):
    months = { "January":1, "February":2, "March":3, "April":4, "May":5, "June":6, "July":7, "August":8, "September":9, "October":10, "November":11, "December":12 }
    [ day, month, year ] = str.split("-")
    return datetime(int(year),months[month],int(day))

class XSLTransformer:

    def __init__(self, stylesheet):
        # instanciate stylesheet object
        styledoc = libxml2.parseFile(stylesheet)
        self.__style = libxslt.parseStylesheetDoc(styledoc)

    def process (self, xml):
        try:
            doc = libxml2.parseDoc(xml)
        except:
            return _("""_("error parsing xml"):\n <pre>%s</pre>""") % xml.replace("<","&lt;")
        # compute the transformation
        result = self.__style.applyStylesheet(doc, None)
        output = self.__style.saveResultToString(result)
        # free memory
        self.__style.freeStylesheet()
        doc.freeDoc()
        result.freeDoc()
        #libxslt.cleanupGlobals() # this line causes mod_python to segfault
        libxml2.cleanupParser()
        return output

class outputGenerator:
    """
    this class generates the application standard XML (getBasicXML)
    and also provides a method to format it using an XSLt stylesheet
    (getFormattedOutput method)
    """

    def __init__(self, aw, XG = None, dataInt=None):
        self.__aw = aw
        if XG != None:
            self._XMLGen = XG
        else:
            self._XMLGen = XMLGen()
        self._config = Config.getInstance()
        self.iconfNamespace = self._config.getIconfNamespace()
        self.iconfXSD = self._config.getIconfXSD()
        self.text = ""
        self.dataInt = dataInt
        self.time_XML = 0
        self.time_HTML = 0

        if dataInt:
            self.cache = ProtectedXMLCache(dataInt)
        else:
            self.cache = XMLCache()

        from MaKaC.webinterface.webFactoryRegistry import WebFactoryRegistry
        self.webFactory = WebFactoryRegistry()

    def _generateMaterialList(self, obj):
        """
        Generates a list containing all the materials, with the
        corresponding Ids for those that already exist
        """

        # yes, this may look a bit redundant, but materialRegistry isn't
        # bound to a particular target
        materialRegistry = obj.getMaterialRegistry()
        return materialRegistry.getMaterialList(obj.getConference())


    def getOutput(self, conf, stylesheet, vars=None, includeSession=1,includeContribution=1,includeMaterial=1,showSession="all",showDate="all",showContribution="all"):
        # get xml conference
        start_time_XML = time.time()
        xml = self._getBasicXML(conf, vars, includeSession,includeContribution,includeMaterial,showSession,showDate,showContribution)
        end_time_XML = start_time_HTML = time.time()
        if not os.path.exists(stylesheet):
            self.text = _("Cannot find stylesheet")
        if os.path.basename(stylesheet) == "xml.xsl":
            self.text = xml
        else:
            # instanciate the XSL tool
            try:
                parser = XSLTransformer(stylesheet)
                self.text = parser.process(xml)
            except Exception, e:
                self.text = _("Cannot parse stylesheet: %s") % str(e)
        end_time_HTML = time.time()
        self.time_XML = end_time_XML - start_time_XML
        self.time_HTML = end_time_HTML - start_time_HTML
        return self.text


    def getFormattedOutput(self, conf, stylesheet, vars=None, includeSession=1,includeContribution=1,includeMaterial=1,showSession="all",showDate="all",showContribution="all"):
        """
        conf: conference object
        stylesheet: path to the xsl file
        """
        self.getOutput(conf, stylesheet, vars, includeSession,includeContribution,includeMaterial,showSession,showDate,showContribution)
        html = self.text
        if DEVELOPMENT:
            stat_text = _("""<br><br><font size="-2">_("XML creation"): %s<br>_("HTML creation"): %s</font>""") % (self.time_XML,self.time_HTML)
        else:
            stat_text = ""
        if (re.search("xml.xsl$",stylesheet) or re.search("text.xsl$",stylesheet) or re.search("jacow.xsl$",stylesheet)) and vars.get("frame","") != "no":
            return "<pre>%s</pre>" % html.replace("<","&lt;") + stat_text
        else:
            return html + stat_text

    def _getBasicXML(self, conf, vars,includeSession,includeContribution,includeMaterial,showSession="all",showDate="all",showContribution="all", out=None):
        if not out:
            out = self._XMLGen
        """
        conf: conference object
        """
        #out.initXml()
        out.openTag("iconf")
        self._confToXML(conf,vars,includeSession,includeContribution,includeMaterial,showSession,showDate, showContribution,out=out)
        out.closeTag("iconf")
        return out.getXml()

    def _userToXML(self, user, out):
        out.openTag("user")
        out.writeTag("title",user.getTitle())
        out.writeTag("name","",[["first",user.getFirstName()],["middle",""],["last",user.getFamilyName()]])
        out.writeTag("organization",user.getAffiliation())
        out.writeTag("email",user.getEmail())
        try:
            out.writeTag("userid",user.id)
        except:
            pass
        out.closeTag("user")

    def _getRoom(self, room, location):
        # get the name that is saved
        roomName = room.getName()

        # if there is a connection to the room booking DB
        if CrossLocationDB.isConnected() and location:
            # get the room info
            roomFromDB = CrossLocationQueries.getRooms( roomName = roomName, location = location.getName() )
            #roomFromDB can be a list or an object room
            if isinstance(roomFromDB,list) and roomFromDB != []:
                roomFromDB = roomFromDB[0]
            # If there's a room with such name.
            # Sometimes CrossLocationQueries.getRooms returns a list with None elements
            if roomFromDB:
                # use the full name instead
                roomName = roomFromDB.getFullName()
        return roomName


    def _confToXML(self, conf, vars, includeSession=1, includeContribution=1, includeMaterial=1, showSession="all", showDate="all",showContribution="all", showWithdrawed=True, useSchedule=True, out=None):
        if not out:
            out = self._XMLGen

        if vars and vars.has_key("frame") and vars["frame"] == "no":
            modificons = 0
        else:
            modificons = 1

        out.writeTag("ID",conf.getId())

        if conf.getOwnerList():
            out.writeTag("category",conf.getOwnerList()[0].getName())
        else:
            out.writeTag("category","")

        out.writeTag("parentProtection", simplejson.dumps(conf.getAccessController().isProtected()))
        out.writeTag("materialList", simplejson.dumps(self._generateMaterialList(conf)))

        if conf.canModify( self.__aw ) and vars and modificons:
            out.writeTag("modifyLink",vars["modifyURL"])
        if conf.canModify( self.__aw ) and vars and modificons:
            out.writeTag("minutesLink",True)
        if conf.canModify( self.__aw ) and vars and modificons:
            out.writeTag("materialLink", True)
        if conf.canModify( self.__aw ) and vars and vars.has_key("cloneURL") and modificons:
            out.writeTag("cloneLink",vars["cloneURL"])
        if  vars and vars.has_key("iCalURL"):
            out.writeTag("iCalLink",vars["iCalURL"])
        if  vars and vars.has_key("webcastAdminURL"):
            out.writeTag("webcastAdminLink",vars["webcastAdminURL"])

        if conf.getOrgText() != "":
            out.writeTag("organiser", conf.getOrgText())

        out.openTag("announcer")
        chair = conf.getCreator()
        if chair != None:
            self._userToXML(chair, out)
        out.closeTag("announcer")

        if conf.getSupportEmail() != '':
            out.writeTag("supportEmail", conf.getSupportEmail(), [["caption", displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(conf).getSupportEmailCaption()]])

        rnh = conf.getReportNumberHolder()
        rns = rnh.listReportNumbers()
        if len(rns) != 0:
            for rn in rns:
                out.openTag("repno")
                out.writeTag("system",rn[0])
                out.writeTag("rn",rn[1])
                out.closeTag("repno")

        out.writeTag("title",conf.getTitle())

        out.writeTag("description",conf.getDescription())

        if conf.getParticipation().displayParticipantList() :
            out.writeTag("participants",conf.getParticipation().getPresentParticipantListText())
        if (conf.getType() == "meeting" or conf.getType() == "simple_event") and conf.getParticipation().isAllowedForApplying() and conf.getStartDate() > nowutc():
            out.writeTag("apply",urlHandlers.UHConfParticipantsNewPending.getURL(conf))

        evaluation = conf.getEvaluation()
        if evaluation.isVisible() and evaluation.inEvaluationPeriod() and evaluation.getNbOfQuestions()>0 :
            out.writeTag("evaluationLink",urlHandlers.UHConfEvaluationDisplay.getURL(conf))

#        if len(conf.getBookingsList()):
#            out.openTag("videoconference")
#            for b in conf.getBookingsList():
#                out.openTag(b.getSystem())
#                if b.getSystem() == "VRVS":
#                    out.writeTag("description",b.getPublicDescription())
#                out.closeTag(b.getSystem())
#            out.closeTag("videoconference")

        if conf.getLocationList()!=[] or conf.getRoom():
            out.openTag("location")
            loc=None
            for l in conf.getLocationList():
                if l.getName() != "":
                    loc=l
                out.writeTag("name",l.getName())
                out.writeTag("address",l.getAddress())
            if conf.getRoom():
                roomName = self._getRoom(conf.getRoom(), loc)
                out.writeTag("room", roomName)
                url=RoomLinker().getURL(conf.getRoom(), loc)
                if url != "":
                    out.writeTag("roomMapURL",url)
            else:
                out.writeTag("room","")
            out.closeTag("location")

        tzUtil = DisplayTZ(self.__aw,conf)
        tz = tzUtil.getDisplayTZ()
        adjusted_startDate = conf.getAdjustedStartDate(tz)
        adjusted_endDate = conf.getAdjustedEndDate(tz)
        out.writeTag("startDate","%d-%s-%sT%s:%s:00" %(adjusted_startDate.year, string.zfill(adjusted_startDate.month,2), string.zfill(adjusted_startDate.day,2), string.zfill(adjusted_startDate.hour,2), string.zfill(adjusted_startDate.minute,2)))
        out.writeTag("endDate","%d-%s-%sT%s:%s:00" %(adjusted_endDate.year, string.zfill(adjusted_endDate.month,2), string.zfill(adjusted_endDate.day,2), string.zfill(adjusted_endDate.hour,2), string.zfill(adjusted_endDate.minute,2)))
        out.writeTag("creationDate",conf.getCreationDate().astimezone(timezone(tz)).strftime("%Y-%m-%dT%H:%M:%S"))
        out.writeTag("modificationDate",conf.getModificationDate().strftime("%Y-%m-%dT%H:%M:%S"))
        out.writeTag("timezone","%s" %(tz))

        uList = conf.getChairList()
        if len(uList) > 0 or conf.getChairmanText() != "":
            out.openTag("chair")
            for chair in uList:
                self._userToXML(chair, out)
            if conf.getChairmanText() != "":
                out.writeTag("UnformatedUser",conf.getChairmanText())
            out.closeTag("chair")

        if showContribution != "all" and conf.getContributionById(showContribution) != None:
            self._contribToXML(conf.getContributionById(showContribution),vars,includeMaterial,conf, out=out)
        elif useSchedule:
            confSchedule = conf.getSchedule()
            if showDate == "all":
                entrylist = confSchedule.getEntries()
            else:
                entrylist = confSchedule.getEntriesOnDay(timezone(tz).localize(stringToDate(showDate)))
            for entry in entrylist:
                if type(entry) is schedule.BreakTimeSchEntry: #TODO: schedule.BreakTimeSchEntry doesn't seem to exist!
                    self._breakToXML(entry, out=out)
                elif type(entry) is conference.ContribSchEntry:
                    owner = entry.getOwner()
                    if owner.canView(self.__aw):
                        if includeContribution:
                            if showWithdrawed or not isinstance(owner.getCurrentStatus(), conference.ContribStatusWithdrawn):
                                self._contribToXML(owner,vars,includeMaterial,conf, out=out)
                elif type(entry) is schedule.LinkedTimeSchEntry: #TODO: schedule.LinkedTimeSchEntry doesn't seem to exist!
                    owner = entry.getOwner()
                    if type(owner) is conference.Contribution:
                        if owner.canView(self.__aw):
                            if includeContribution:
                                if showWithdrawed or not isinstance(owner.getCurrentStatus(), conference.ContribStatusWithdrawn):
                                    self._contribToXML(owner,vars,includeMaterial,conf, out=out)
                    elif type(owner) is conference.Session:
                        if owner.canView(self.__aw):
                            if includeSession and (showSession == "all" or owner.getId() == showSession):
                                self._sessionToXML(owner,vars,includeContribution,includeMaterial, showWithdrawed=showWithdrawed, out=out)
                    elif type(owner) is conference.SessionSlot:
                        if owner.getSession().canView(self.__aw):
                            if includeSession and (showSession == "all" or owner.getSession().getId() == showSession):
                                self._slotToXML(owner,vars,includeContribution,includeMaterial, showWithdrawed=showWithdrawed, out=out)
        else:
            confSchedule = conf.getSchedule()
            for entry in confSchedule.getEntries():
                if type(entry) is conference.ContribSchEntry:
                    owner = entry.getOwner()
                    if owner.canView(self.__aw):
                        if includeContribution:
                            self._contribToXML(owner,vars,includeMaterial,conf,out=out)
            sessionList = conf.getSessionList()
            for session in sessionList:
                if session.canAccess(self.__aw) and includeSession:
                    self._sessionToXML(session, vars, includeContribution, includeMaterial, showWithdrawed=showWithdrawed, useSchedule=False, out=out)

        mList = conf.getAllMaterialList()
        for mat in mList:
            if mat.canView(self.__aw) and mat.getTitle() != "Internal Page Files":
                if includeMaterial:
                    self._materialToXML(mat, vars, out=out)

        wm = webcast.HelperWebcastManager.getWebcastManagerInstance()
        url = wm.isOnAir(conf)
        if url:
            out.openTag("material")
            out.writeTag("ID","live webcast")
            out.writeTag("title","live webcast")
            out.writeTag("description","")
            out.writeTag("type","")
            out.writeTag("displayURL",url)
            out.closeTag("material")
        elif wm.getForthcomingWebcast(conf):
            out.openTag("material")
            out.writeTag("ID","forthcoming webcast")
            out.writeTag("title","forthcoming webcast")
            out.writeTag("description","")
            out.writeTag("type","")
            out.writeTag("displayURL", wm.getWebcastServiceURL())
            out.closeTag("material")

        #plugins XML
        out.openTag("plugins")
        if PluginsHolder().hasPluginType("Collaboration"):
            from MaKaC.plugins.Collaboration.output import OutputGenerator
            OutputGenerator.collaborationToXML(out, conf, tz)
        out.closeTag("plugins")



    def _sessionToXML(self,session,vars,includeContribution,includeMaterial, showWithdrawed=True, useSchedule=True, out=None):
        if not out:
            out = self._XMLGen
        if vars and vars.has_key("frame") and vars["frame"] == "no":
            modificons = 0
        else:
            modificons = 1
        out.openTag("session")
        out.writeTag("ID",session.getId())

        if session.getCode() not in ["no code", ""]:
            out.writeTag("code",session.getCode())
        else:
            out.writeTag("code",session.getId())
        if (session.canModify( self.__aw ) or session.canCoordinate(self.__aw)) and vars and modificons:
            out.writeTag("modifyLink",vars["sessionModifyURLGen"](session))
        if (session.canModify( self.__aw ) or session.canCoordinate(self.__aw)) and vars and modificons:
            out.writeTag("minutesLink",True)
            out.writeTag("materialLink", True)
        out.writeTag("title",session.title)
        out.writeTag("description",session.description)
        cList = session.getConvenerList()
        if len(cList) != 0:
            out.openTag("convener")
            for conv in cList:
                self._userToXML(conv, out)
            if session.getConvenerText() != "":
                out.writeTag("UnformatedUser",session.getConvenerText())
            out.closeTag("convener")
        l = session.getLocation()
        if l!=None or session.getRoom():
            out.openTag("location")
            if l!=None:
                out.writeTag("name",l.getName())
                out.writeTag("address",l.getAddress())
            if session.getRoom():
                roomName = self._getRoom(session.getRoom(), l)
                out.writeTag("room", roomName)
                url=RoomLinker().getURL(session.getRoom(), l)
                if url != "":
                    out.writeTag("roomMapURL",url)
            else:
                out.writeTag("room","")
            out.closeTag("location")
        try:
            displayMode = self.__aw._currentUser.getDisplayTZMode()
        except:
            # not logged in, use meeting timezone
            displayMode = 'Meeting'
        if displayMode == 'Meeting':
            tz = self.conf.getTimezone()
        else:
            tz = self.__aw._currentUser.getTimezone()
        startDate = session.getStartDate().astimezone(timezone(tz))
        out.writeTag("startDate","%d-%s-%sT%s:%s:00" %(startDate.year, string.zfill(startDate.month,2), string.zfill(startDate.day,2),string.zfill(startDate.hour,2), string.zfill(startDate.minute,2)))
        endDate = session.startDate + session.duration
        out.writeTag("endDate","%d-%s-%sT%s:%s:00" %(endDate.year, string.zfill(endDate.month,2), string.zfill(endDate.day,2),string.zfill(endDate.hour,2), string.zfill(endDate.minute,2)))
        out.writeTag("duration","%s:%s" %(string.zfill((datetime(1900,1,1)+session.duration).hour,2), string.zfill((datetime(1900,1,1)+session.duration).minute,2)))
        if includeContribution:
            if useSchedule:
                sessionSchedule = session.getSchedule()
                for entry in sessionSchedule.getEntries():
                    if type(entry) is schedule.BreakTimeSchEntry: #TODO: schedule.BreakTimeSchEntry doesn't seem to exist!
                        self._breakToXML(entry, out=out)
                    elif type(entry) is schedule.LinkedTimeSchEntry: #TODO: schedule.LinkedTimeSchEntry doesn't seem to exist!
                        owner = entry.getOwner()
                        if type(owner) is conference.Contribution:
                            if owner.canView(self.__aw):
                                if showWithdrawed or not isinstance(owner.getCurrentStatus(), conference.ContribStatusWithdrawn):
                                    self._contribToXML(owner,vars,includeMaterial, conf,out=out)
            else:
                for contrib in session.getContributionList():
                    if contrib.canView(self.__aw):
                        if showWithdrawed or not isinstance(contrib.getCurrentStatus(), conference.ContribStatusWithdrawn):
                            self._contribToXML(contrib, vars, includeMaterial, conf,out=out)

        mList = session.getAllMaterialList()
        for mat in mList:
            self._materialToXML(mat, vars, out=out)
        out.closeTag("session")



    def _slotToXML(self,slot,vars,includeContribution,includeMaterial, showWithdrawed=True, out=None):
        if not out:
            out = self._XMLGen
        session = slot.getSession()
        conf = session.getConference()
        if vars and vars.has_key("frame") and vars["frame"] == "no":
            modificons = 0
        else:
            modificons = 1
        out.openTag("session")
        out.writeTag("ID",session.getId())

        out.writeTag("parentProtection", simplejson.dumps(session.getAccessController().isProtected()))
        out.writeTag("materialList", simplejson.dumps(self._generateMaterialList(session)))


        slotCode = session.getSortedSlotList().index(slot) + 1
        if session.getCode() not in ["no code", ""]:
            out.writeTag("code","%s-%s" % (session.getCode(),slotCode))
        else:
            out.writeTag("code","sess%s-%s" % (session.getId(),slotCode))
        if (session.canModify( self.__aw ) or session.canCoordinate(self.__aw)) and vars and modificons:
            out.writeTag("modifyLink",vars["sessionModifyURLGen"](session))
        if (session.canModify( self.__aw ) or session.canCoordinate(self.__aw)) and vars and modificons:
            out.writeTag("minutesLink",True)
            out.writeTag("materialLink", True)
        title = session.title
        if slot.getTitle() != "" and slot.getTitle() != title:
            title += ": %s" %  slot.getTitle()
        out.writeTag("title",title)
        out.writeTag("description",session.description)
        cList = slot.getConvenerList()
        if len(cList) != 0:
            out.openTag("convener")
            for conv in cList:
                self._userToXML(conv, out)
            if session.getConvenerText() != "":
                out.writeTag("UnformatedUser",session.getConvenerText())
            out.closeTag("convener")
        l = slot.getLocation()
        room = slot.getRoom()
        if not conf.getEnableSessionSlots():
            l = session.getLocation()
            room = session.getRoom()
        if l!=None or room:
            out.openTag("location")
            if l!=None:
                out.writeTag("name",l.getName())
                out.writeTag("address",l.getAddress())
            if room:
                roomName = self._getRoom(room, l)
                out.writeTag("room", roomName)
                url=RoomLinker().getURL(room, l)
                if url != "":
                    out.writeTag("roomMapURL",url)
            else:
                out.writeTag("room","")
            out.closeTag("location")
        tzUtil = DisplayTZ(self.__aw,conf)
        tz = tzUtil.getDisplayTZ()
        startDate = slot.getStartDate().astimezone(timezone(tz))
        endDate = slot.getEndDate().astimezone(timezone(tz))
        out.writeTag("startDate","%d-%s-%sT%s:%s:00" %(startDate.year, string.zfill(startDate.month,2), string.zfill(startDate.day,2),string.zfill(startDate.hour,2), string.zfill(startDate.minute,2)))
        out.writeTag("endDate","%d-%s-%sT%s:%s:00" %(endDate.year, string.zfill(endDate.month,2), string.zfill(endDate.day,2),string.zfill(endDate.hour,2), string.zfill(endDate.minute,2)))
        out.writeTag("duration","%s:%s" %(string.zfill((datetime(1900,1,1)+slot.duration).hour,2), string.zfill((datetime(1900,1,1)+slot.duration).minute,2)))
        if includeContribution:
            for entry in slot.getSchedule().getEntries():
                if type(entry) is schedule.BreakTimeSchEntry: #TODO: schedule.BreakTimeSchEntry doesn't seem to exist!
                    self._breakToXML(entry, out=out)
                else:
                    owner = entry.getOwner()
                    if isinstance(owner, conference.AcceptedContribution) or isinstance(owner, conference.Contribution):
                        if owner.canView(self.__aw):
                            if showWithdrawed or not isinstance(owner.getCurrentStatus(), conference.ContribStatusWithdrawn):
                                self._contribToXML(owner,vars,includeMaterial, conf,out=out)
        mList = session.getAllMaterialList()
        for mat in mList:
            self._materialToXML(mat, vars, out=out)
        out.closeTag("session")



    def _contribToXML(self,cont,vars,includeMaterial, conf, out=None):
        if not out:
            out = self._XMLGen
        if vars and vars.has_key("frame") and vars["frame"] == "no":
            modificons = 0
        else:
            modificons = 1
        out.openTag("contribution")
        out.writeTag("ID",cont.getId())

        out.writeTag("parentProtection", simplejson.dumps(cont.getAccessController().isProtected()))
        out.writeTag("materialList", simplejson.dumps(self._generateMaterialList(cont)))

        if cont.getBoardNumber() != "":
            out.writeTag("board",cont.getBoardNumber())
        if cont.getTrack() != None:
            out.writeTag("track",cont.getTrack().getTitle())
        if cont.getType() != None:
            out.openTag("type")
            out.writeTag("id",cont.getType().getId())
            out.writeTag("name",cont.getType().getName())
            out.closeTag("type")
        if cont.canModify( self.__aw ) and vars and modificons:
            out.writeTag("modifyLink",vars["contribModifyURLGen"](cont))
        if (cont.canModify( self.__aw ) or cont.canUserSubmit(self.__aw.getUser())) and vars and modificons:
            out.writeTag("minutesLink", True)
        if (cont.canModify( self.__aw ) or cont.canUserSubmit(self.__aw.getUser())) and vars and modificons:
            out.writeTag("materialLink", True)
        keywords = cont.getKeywords()
        keywords.replace("\r\n", "\n")
        for keyword in keywords.split("\n"):
            out.writeTag("keyword",keyword.strip())
        rnh = cont.getReportNumberHolder()
        rns = rnh.listReportNumbers()
        if len(rns) != 0:
            for rn in rns:
                out.openTag("repno")
                out.writeTag("system",rn[0])
                out.writeTag("rn",rn[1])
                out.closeTag("repno")
        out.writeTag("title",cont.title)
        sList = cont.getSpeakerList()
        if len(sList) != 0:
            out.openTag("speakers")
            for sp in sList:
                self._userToXML(sp, out)
            if cont.getSpeakerText() != "":
                out.writeTag("UnformatedUser",cont.getSpeakerText())
            out.closeTag("speakers")
        primaryAuthorList = cont.getPrimaryAuthorList()
        if len(primaryAuthorList) != 0:
            out.openTag("primaryAuthors")
            for sp in primaryAuthorList:
                self._userToXML(sp, out)
            out.closeTag("primaryAuthors")
        coAuthorList = cont.getCoAuthorList()
        if len(coAuthorList) != 0:
            out.openTag("coAuthors")
            for sp in coAuthorList:
                self._userToXML(sp, out)
            out.closeTag("coAuthors")
        l = cont.getLocation()
        if l != None or cont.getRoom():
            out.openTag("location")
            if l!=None:
                out.writeTag("name",l.getName())
                out.writeTag("address",l.getAddress())
            if cont.getRoom():
                roomName = self._getRoom(cont.getRoom(), l)
                out.writeTag("room", roomName)
                url=RoomLinker().getURL(cont.getRoom(), l)
                if url != "":
                    out.writeTag("roomMapURL",url)
            else:
                out.writeTag("room","")
            out.closeTag("location")
        tzUtil = DisplayTZ(self.__aw,conf)
        tz = tzUtil.getDisplayTZ()

        startDate = None
        if cont.startDate:
            startDate = cont.startDate.astimezone(timezone(tz))

        if startDate:
            endDate = startDate + cont.duration
            out.writeTag("startDate","%d-%s-%sT%s:%s:00" %(startDate.year, string.zfill(startDate.month,2), string.zfill(startDate.day,2),string.zfill(startDate.hour,2), string.zfill(startDate.minute,2)))
            out.writeTag("endDate","%d-%s-%sT%s:%s:00" %(endDate.year, string.zfill(endDate.month,2), string.zfill(endDate.day,2),string.zfill(endDate.hour,2), string.zfill(endDate.minute,2)))
        if cont.duration:
            out.writeTag("duration","%s:%s" %(string.zfill((datetime(1900,1,1)+cont.duration).hour,2), string.zfill((datetime(1900,1,1)+cont.duration).minute,2)))
        out.writeTag("abstract",cont.getDescription())
        matList = cont.getAllMaterialList()
        for mat in matList:
            if mat.canView(self.__aw):
                if includeMaterial:
                    self._materialToXML(mat, vars, out=out)
                else:
                    out.writeTag("material",out.writeTag("id",mat.id))
        for subC in cont.getSubContributionList():
            self._subContributionToXML(subC,vars,includeMaterial, out=out)
        out.closeTag("contribution")


    def _subContributionToXML(self, subCont, vars, includeMaterial, out=None):
        if not out:
            out = self._XMLGen
        if vars and vars.has_key("frame") and vars["frame"] == "no":
            modificons = 0
        else:
            modificons = 1
        out.openTag("subcontribution")
        out.writeTag("ID",subCont.getId())

        out.writeTag("parentProtection", simplejson.dumps(subCont.getContribution().getAccessController().isProtected()))
        out.writeTag("materialList", simplejson.dumps(self._generateMaterialList(subCont)))

        if subCont.canModify( self.__aw ) and vars and modificons:
            out.writeTag("modifyLink",vars["subContribModifyURLGen"](subCont))
        if (subCont.canModify( self.__aw ) or subCont.canUserSubmit( self.__aw.getUser())) and vars and modificons:
            out.writeTag("minutesLink",True)
        if (subCont.canModify( self.__aw ) or subCont.canUserSubmit( self.__aw.getUser())) and vars and modificons:
            out.writeTag("materialLink", True)
        rnh = subCont.getReportNumberHolder()
        rns = rnh.listReportNumbers()
        if len(rns) != 0:
            for rn in rns:
                out.openTag("repno")
                out.writeTag("system",rn[0])
                out.writeTag("rn",rn[1])
                out.closeTag("repno")
        out.writeTag("title",subCont.title)
        sList = subCont.getSpeakerList()
        if len(sList) > 0 or subCont.getSpeakerText() != "":
            out.openTag("speakers")
        for sp in sList:
            self._userToXML(sp, out)
        if subCont.getSpeakerText() != "":
            out.writeTag("UnformatedUser",subCont.getSpeakerText())
        if len(sList) > 0 or subCont.getSpeakerText() != "":
            out.closeTag("speakers")
        out.writeTag("duration","%s:%s"%((string.zfill((datetime(1900,1,1)+subCont.getDuration()).hour,2), string.zfill((datetime(1900,1,1)+subCont.getDuration()).minute,2))))
        out.writeTag("abstract",subCont.getDescription())
        matList = subCont.getAllMaterialList()
        for mat in matList:
            if mat.canView(self.__aw):
                if includeMaterial:
                    self._materialToXML(mat, vars, out=out)
        out.closeTag("subcontribution")


    def _materialToXML(self,mat, vars, out=None):
        if not out:
            out = self._XMLGen
        out.openTag("material")
        out.writeTag("ID",mat.getId())
        out.writeTag("title",mat.title)
        out.writeTag("description",mat.description)
        out.writeTag("type",mat.type)
        if vars:
            out.writeTag("displayURL",vars["materialURLGen"](mat))
        from MaKaC.conference import Minutes
        if isinstance(mat, Minutes):
            out.writeTag("minutesText",mat.getText())
        pdfs = []
        docs = []
        ppts = []
        odps = []
        odts = []
        odss = []
        others = []
        links = []
        if len(mat.getResourceList()) > 0:
            out.openTag("files")
            for res in mat.getResourceList():
                try:
                    type = res.getFileType().lower()
                    if type=="pdf":
                        pdfs.append(res)
                    elif type=="doc" or type == "docx":
                        docs.append(res)
                    elif type=="ppt" or type == "pptx":
                        ppts.append(res)
                    elif type=="sxi" or type=="odp":
                        odps.append(res)
                    elif type=="sxw" or type=="odt":
                        odts.append(res)
                    elif type=="sxc" or type=="ods":
                        odss.append(res)
                    else:
                        others.append(res)
                    if vars:
                        out.openTag("file")
                        out.writeTag("name",res.getFileName())
                        out.writeTag("type",res.getFileType().lower())
                        out.writeTag("url",vars["resourceURLGen"](res))
                        out.closeTag("file")
                except:
                    links.append(res)
            out.closeTag("files")
            if not len(pdfs) > 1 and not len(docs) > 1 and not len(ppts) > 1 and not len(odps) > 1 and not len(odts) > 1 and not len(odss) > 1 and len(others) == 0 and not len(links) > 1:
                if vars:
                    if len(pdfs)==1:
                        out.writeTag("pdf",vars["resourceURLGen"](pdfs[0]))
                    if len(docs)==1:
                        out.writeTag("doc",vars["resourceURLGen"](docs[0]))
                    if len(ppts)==1:
                        out.writeTag("ppt",vars["resourceURLGen"](ppts[0]))
                    if len(odps)==1:
                        out.writeTag("odp",vars["resourceURLGen"](odps[0]))
                    if len(odts)==1:
                        out.writeTag("odt",vars["resourceURLGen"](odts[0]))
                    if len(odss)==1:
                        out.writeTag("ods",vars["resourceURLGen"](odss[0]))
                if len(links)==1:
                    out.writeTag("link",str(links[0].getURL()))
        if mat.isItselfProtected():
            out.writeTag("locked","yes")
        out.closeTag("material")

    def _resourcesToXML(self, rList, out=None):
        if not out:
            out = self._XMLGen
        out.openTag("resources")
        for res in rList:
            if res.canView(self.__aw):
                self._resourceToXML(res, out=out)
        out.closeTag("resources")

    def _resourceToXML(self,res, out=None):
        if not out:
            out = self._XMLGen
        if type(res) == conference.LocalFile:
            self._resourceFileToXML(res, out=out)
        else:
            self._resourceLinkToXML(res, out=out)

    def _resourceLinkToXML(self,res, out=None):
        if not out:
            out = self._XMLGen
        out.openTag("resourceLink")
        out.writeTag("name",res.getName())
        out.writeTag("description",res.getDescription())
        out.writeTag("url",res.getURL())
        out.closeTag("resourceLink")

    def _resourceFileToXML(self,res, out=None):
        if not out:
            out = self._XMLGen
        out.openTag("resourceFile")
        out.writeTag("name",res.getName())
        out.writeTag("description",res.getDescription())
        out.writeTag("type",res.fileType)
        out.writeTag("url",res.getURL())
        out.writeTag("fileName",res.getFileName())
        out.writeTag("duration","1")#TODO:DURATION ISN'T ESTABLISHED
        cDate = res.getCreationDate()
        creationDateStr = "%d-%s-%sT%s:%s:00Z" %(cDate.year, string.zfill(cDate.month,2), string.zfill(cDate.day,2), string.zfill(cDate.hour,2), string.zfill(cDate.minute,2))
        out.writeTag("creationDate",creationDateStr)
        out.closeTag("resourceFile")

    def _breakToXML(self,br, out=None):
        if not out:
            out = self._XMLGen
        out.openTag("break")
        out.writeTag("name",br.getTitle())
        tzUtil = DisplayTZ(self.__aw,br.getOwner())
        tz = tzUtil.getDisplayTZ()
        startDate = br.getStartDate().astimezone(timezone(tz))
        endDate = br.getEndDate().astimezone(timezone(tz))
        out.writeTag("startDate","%d-%s-%sT%s:%s" %(startDate.year, string.zfill(startDate.month,2), string.zfill(startDate.day,2),string.zfill(startDate.hour,2), string.zfill(startDate.minute,2)))
        out.writeTag("endDate","%d-%s-%sT%s:%s" %(endDate.year, string.zfill(endDate.month,2), string.zfill(endDate.day,2),string.zfill(endDate.hour,2), string.zfill(endDate.minute,2)))
        out.writeTag("duration","%s:%s"%((string.zfill((datetime(1900,1,1)+br.getDuration()).hour,2), string.zfill((datetime(1900,1,1)+br.getDuration()).minute,2))))
        if br.getDescription() != "":
            out.writeTag("description", br.getDescription())
        l = br.getLocation()
        if l != None or br.getRoom():
            out.openTag("location")
            if l!=None:
                out.writeTag("name",l.getName())
                out.writeTag("address",l.getAddress())
            if br.getRoom():
                roomName = self._getRoom(br.getRoom(), l)
                out.writeTag("room", roomName)
                url=RoomLinker().getURL(br.getRoom(), l)
                if url != "":
                    out.writeTag("roomMapURL",url)
            else:
                out.writeTag("room","")
            out.closeTag("location")
        out.closeTag("break")


    def confToXML(self,conf,includeSession,includeContribution,includeMaterial,showSession="all", showContribution="all", out=None, forceCache=False):
        if not out:
            out = self._XMLGen
        #try to get a cache
        version = "ses-%s_cont-%s_mat-%s_sch-%s"%(includeSession,includeContribution,includeMaterial,False)
        obj = None
        if not forceCache:
            obj = self.cache.loadObject(version, conf)
        if obj:
            xml = obj.getContent()
        else:
            temp = XMLGen(init=False)
            self._confToXML(conf,None,includeSession,includeContribution,includeMaterial,showSession=showSession, showDate="all", showContribution=showContribution, showWithdrawed=False, useSchedule=False, out=temp)
            xml = temp.getXml()
            self.cache.cacheObject(version, xml, conf)
        #    out.writeTag("cache", "not found in cache")
        #else:
        #    out.writeTag("cache", "found in cache")

        out.writeXML(xml)
        #return xml



    #fb

    def confToXMLMarc21(self,conf,includeSession=1,includeContribution=1,includeMaterial=1,out=None, forceCache=False):

        if not out:
            out = self._XMLGen
        #try to get a cache
        version = "MARC21_ses-%s_cont-%s_mat-%s"%(includeSession,includeContribution,includeMaterial)
        obj = None
        if not forceCache:
            obj = self.cache.loadObject(version, conf)
        if obj:
            xml = obj.getContent()
        else:
            # No cache, build the XML
            temp = XMLGen(init=False)
            self._confToXMLMarc21(conf,includeSession,includeContribution,includeMaterial, out=temp)
            xml = temp.getXml()
            # save XML in cache
            self.cache.cacheObject(version, xml, conf)
        out.writeXML(xml)

    def _confToXMLMarc21(self,conf,includeSession=1,includeContribution=1,includeMaterial=1,out=None):
        if not out:
            out = self._XMLGen

        out.openTag("marc:datafield",[["tag","245"],["ind1"," "],["ind2"," "]])
        out.writeTag("marc:subfield",conf.getTitle(),[["code","a"]])
        out.closeTag("marc:datafield")

        out.writeTag("marc:leader", "00000nmm  2200000uu 4500")
        out.openTag("marc:datafield",[["tag","111"],["ind1"," "],["ind2"," "]])
        out.writeTag("marc:subfield",conf.title,[["code","a"]])

        # XXX: If there is ROOM and not LOCATION....There will be information missed.
        for l in conf.getLocationList():
            loc = ""
            if l.getName() != "":
                loc = conf.getLocation().getName()
            if l.getAddress() != "":
                loc = loc +", "+conf.getLocation().getAddress()

            if conf.getRoom():
                roomName = self._getRoom(conf.getRoom(), l)
                loc = loc + ", " + roomName

            if l.getName() != "":
                out.writeTag("marc:subfield",loc,[["code","c"]])


        #out.writeTag("marc:subfield","%d-%s-%sT%s:%s:00Z" %(conf.getStartDate().year, string.zfill(conf.getStartDate().month,2), string.zfill(conf.getStartDate().day,2), string.zfill(conf.getStartDate().hour,2), string.zfill(conf.getStartDate().minute,2)),[["code","9"]])
        #out.writeTag("marc:subfield","%d-%s-%sT%s:%s:00Z" %(conf.getEndDate().year, string.zfill(conf.getEndDate().month,2), string.zfill(conf.getEndDate().day,2), string.zfill(conf.getEndDate().hour,2), string.zfill(conf.getEndDate().minute,2)),[["code","z"]])
        #tz = conf.getTimezone()
        #sd = conf.getAdjustedStartDate(tz)
        #ed = conf.getAdjustedEndDate(tz)
        sd = conf.getStartDate()
        ed = conf.getEndDate()
        out.writeTag("marc:subfield","%d-%s-%sT%s:%s:00Z" %(sd.year, string.zfill(sd.month,2), string.zfill(sd.day,2), string.zfill(sd.hour,2), string.zfill(sd.minute,2)),[["code","9"]])
        out.writeTag("marc:subfield","%d-%s-%sT%s:%s:00Z" %(ed.year, string.zfill(ed.month,2), string.zfill(ed.day,2), string.zfill(ed.hour,2), string.zfill(ed.minute,2)),[["code","z"]])

        out.writeTag("marc:subfield", self.dataInt.objToId(conf),[["code","g"]])
        out.closeTag("marc:datafield")

        for path in conf.getCategoriesPath():
            out.openTag("marc:datafield",[["tag","650"],["ind1"," "],["ind2","7"]])
            out.writeTag("marc:subfield", ":".join(path), [["code","a"]])
            out.closeTag("marc:datafield")

        ####################################
        # Fermi timezone awareness         #
        ####################################
        #if conf.getStartDate() is not None:
        #    out.openTag("marc:datafield",[["tag","518"],["ind1"," "],["ind2"," "]])
        #    out.writeTag("marc:subfield","%d-%s-%sT%s:%s:00Z" %(conf.getStartDate().year, string.zfill(conf.getStartDate().month,2), string.zfill(conf.getStartDate().day,2), string.zfill(conf.getStartDate().hour,2), string.zfill(conf.getStartDate().minute,2)),[["code","d"]])
        #    out.closeTag("marc:datafield")
        #sd = conf.getAdjustedStartDate(tz)
        sd = conf.getStartDate()
        if sd is not None:
            out.openTag("marc:datafield",[["tag","518"],["ind1"," "],["ind2"," "]])
            out.writeTag("marc:subfield","%d-%s-%sT%s:%s:00Z" %(sd.year, string.zfill(sd.month,2), string.zfill(sd.day,2), string.zfill(sd.hour,2), string.zfill(sd.minute,2)),[["code","d"]])
            out.closeTag("marc:datafield")
        ####################################
        # Fermi timezone awareness(end)    #
        ####################################

        out.openTag("marc:datafield",[["tag","520"],["ind1"," "],["ind2"," "]])
        out.writeTag("marc:subfield",conf.getDescription(),[["code","a"]])
        out.closeTag("marc:datafield")

        if conf.getReportNumberHolder().listReportNumbers():
            out.openTag("marc:datafield",[["tag","088"],["ind1"," "],["ind2"," "]])
            for report in conf.getReportNumberHolder().listReportNumbers():
                out.writeTag("marc:subfield",report[1],[["code","a"]])
            out.closeTag("marc:datafield")


        out.openTag("marc:datafield",[["tag","653"],["ind1","1"],["ind2"," "]])
        keywords = conf.getKeywords()
        keywords.replace("\r\n", "\n")
        for keyword in keywords.split("\n"):
            out.writeTag("marc:subfield",keyword,[["code","a"]])
        out.closeTag("marc:datafield")


        import MaKaC.webinterface.simple_event as simple_event
        import MaKaC.webinterface.meeting as meeting
        type = "Conference"
        if self.webFactory.getFactory(conf) == simple_event.WebFactory:
            type = "Lecture"
        elif self.webFactory.getFactory(conf) == meeting.WebFactory:
            type = "Meeting"
        out.openTag("marc:datafield",[["tag","650"],["ind1","2"],["ind2","7"]])
        out.writeTag("marc:subfield",type,[["code","a"]])
        out.closeTag("marc:datafield")
        #### t o d o

        #out.openTag("datafield",[["tag","650"],["ind1","3"],["ind2","7"]])
        #out.writeTag("subfield",,[["code","a"]])
        #out.closeTag("datafield")


        # tag 700 chair name
        uList = conf.getChairList()
        for chair in uList:
            out.openTag("marc:datafield",[["tag","906"],["ind1"," "],["ind2"," "]])
            nom = chair.getFamilyName() + " " + chair.getFirstName()
            out.writeTag("marc:subfield",nom,[["code","p"]])
            out.writeTag("marc:subfield",chair.getAffiliation(),[["code","u"]])
            out.closeTag("marc:datafield")


        #out.openTag("datafield",[["tag","856"],["ind1","4"],["ind2"," "]])
        matList = conf.getAllMaterialList()
        for mat in matList:
            if self.dataInt.isPrivateDataInt() or mat.canView(self.__aw):
                if includeMaterial:
                    self.materialToXMLMarc21(mat, out=out)
        #out.closeTag("datafield")

        #if respEmail != "":
        #    out.openTag("datafield",[["tag","859"],["ind1"," "],["ind2"," "]])
        #   out.writeTag("subfield",respEmail,[["code","f"]])
        #   out.closeTag("datafield")
        # tag 859 email
        uList = conf.getChairList()
        for chair in uList:
            out.openTag("marc:datafield",[["tag","859"],["ind1"," "],["ind2"," "]])
            out.writeTag("marc:subfield",chair.getEmail(),[["code","f"]])
            out.closeTag("marc:datafield")

        edate = conf.getCreationDate()
        creaDate = datetime( edate.year, edate.month, edate.day )

        out.openTag("marc:datafield",[["tag","961"],["ind1"," "],["ind2"," "]])
        out.writeTag("marc:subfield","%d-%s-%sT"%(creaDate.year, string.zfill(creaDate.month,2), string.zfill(creaDate.day,2)),[["code","x"]])
        out.closeTag("marc:datafield")

        edate = conf.getModificationDate()
        modifDate = datetime( edate.year, edate.month, edate.day )

        out.openTag("marc:datafield",[["tag","961"],["ind1"," "],["ind2"," "]])
        out.writeTag("marc:subfield","%d-%s-%sT"%(modifDate.year, string.zfill(modifDate.month,2), string.zfill(modifDate.day,2)),[["code","c"]])
        out.closeTag("marc:datafield")

        out.openTag("marc:datafield",[["tag","980"],["ind1"," "],["ind2"," "]])
        confcont = "Indico"
        out.writeTag("marc:subfield",confcont,[["code","a"]])
        out.closeTag("marc:datafield")

        out.openTag("marc:datafield",[["tag","970"],["ind1"," "],["ind2"," "]])
        out.writeTag("marc:subfield","INDICO." + self.dataInt.objToId(conf),[["code","a"]])
        out.closeTag("marc:datafield")

        out.openTag("marc:datafield",[["tag","856"],["ind1","4"],["ind2"," "]])
        url = str(urlHandlers.UHConferenceDisplay.getURL(conf))
        out.writeTag("marc:subfield",url,[["code","u"]])
        out.writeTag("marc:subfield", "Event details", [["code","y"]])
        out.closeTag("marc:datafield")


# I need to check to see if plugin is activated, and if request is coming from plugin
        # Access control information, if event is protected
        # Get set containing Avatar objects (if empty, that means event is public)
        allowed_avatars = conf.getRecursiveAllowedToAccessList()
        if allowed_avatars is not None and len(allowed_avatars) > 0:
            # Build a list holding email strings instead of Avatar objects
            allowed_emails = []
            for av in allowed_avatars:
                if isinstance(av, Avatar):
                    allowed_emails.append(av.getEmail())
                elif isinstance(av, CERNGroup):
                    allowed_emails.append(av.getId() + " [CERN]")
                else:
                    allowed_emails.append("UNKNOWN: %s" % av.getId())

            out.openTag("marc:datafield",[["tag","506"], ["ind1","1"], ["ind2"," "]])
            out.writeTag("marc:subfield", "Restricted",  [["code", "a"]])
            for email_id in allowed_emails:
                out.writeTag("marc:subfield", email_id,  [["code", "d"]])
            out.writeTag("marc:subfield", "group",       [["code", "f"]])
            out.writeTag("marc:subfield", "CDS Invenio", [["code", "2"]]) # <-- should not be hard coded here
            out.writeTag("marc:subfield", "SzGeCERN",    [["code", "5"]]) # <-- should not be hard coded here
            out.closeTag("marc:datafield")

    ## def sessionToXMLMarc21(self,session,includeMaterial=1, out=None, forceCache=False):
    ##     if not out:
    ##         out = self._XMLGen
    ##     #try to get a cache
    ##     version = "MARC21_mat-%s"%(includeMaterial)
    ##     xml = ""
    ##     if not xml:
    ##         # No cache, build the XML
    ##         temp = XMLGen(init=False)
    ##         self._sessionToXMLMarc21(session,includeMaterial, out=temp)
    ##         xml = temp.getXml()
    ##     out.writeXML(xml)


    ## def _sessionToXMLMarc21(self,session,includeMaterial=1, out=None):
    ##     if not out:
    ##         out = self._XMLGen

    ##     out.writeTag("marc:leader", "00000nmm  2200000uu 4500")
    ##     out.openTag("marc:datafield",[["tag","035"],["ind1"," "],["ind2"," "]])
    ##     out.writeTag("marc:subfield","INDICO%s"%(self.dataInt.objToId(session, separator="."), session.getId()),[["code","a"]])
    ##     out.closeTag("marc:datafield")

    ##     out.openTag("marc:datafield",[["tag","035"],["ind1"," "],["ind2"," "]])
    ##     out.writeTag("marc:subfield",self.dataInt.objToId(session, separator="."),[["code","a"]])
    ##     out.writeTag("marc:subfield","Indico",[["code","9"]])
    ##     out.closeTag("marc:datafield")

    ##     out.openTag("marc:datafield",[["tag","245"],["ind1"," "],["ind2"," "]])
    ##     out.writeTag("marc:subfield",session.getTitle(),[["code","a"]])
    ##     out.closeTag("marc:datafield")

    ##     out.openTag("marc:datafield",[["tag","300"],["ind1"," "],["ind2"," "]])
    ##     out.writeTag("marc:subfield",session.getDuration(),[["code","a"]])
    ##     out.closeTag("marc:datafield")

    ##     out.openTag("marc:datafield",[["tag","111"],["ind1"," "],["ind2"," "]])
    ##     out.writeTag("marc:subfield", self.dataInt.objToId(session.getConference()),[["code","g"]])
    ##     out.closeTag("marc:datafield")

    ##     for path in session.getConference().getCategoriesPath():
    ##         out.openTag("marc:datafield",[["tag","650"],["ind1"," "],["ind2","7"]])
    ##         out.writeTag("marc:subfield", ":".join(path), [["code","a"]])
    ##         out.closeTag("marc:datafield")

    ##     l=session.getLocation()
    ##     if (l and l.getName() != "") or session.getStartDate() is not None:
    ##         out.openTag("marc:datafield",[["tag","518"],["ind1"," "],["ind2"," "]])
    ##         if l:
    ##             if l.getName() != "":
    ##                 out.writeTag("marc:subfield",l.getName(),[["code","r"]])
    ##         if session.getStartDate() is not None:
    ##             out.writeTag("marc:subfield","%d-%s-%sT%s:%s:00Z" %(session.getStartDate().year, string.zfill(session.getStartDate().month,2), string.zfill(session.getStartDate().day,2), string.zfill(session.getStartDate().hour,2), string.zfill(session.getStartDate().minute,2)),[["code","d"]])
    ##             out.writeTag("marc:subfield","%d-%s-%sT%s:%s:00Z" %(session.getEndDate().year, string.zfill(session.getEndDate().month,2), string.zfill(session.getEndDate().day,2), string.zfill(session.getEndDate().hour,2), string.zfill(session.getEndDate().minute,2)),[["code","h"]])
    ##         out.closeTag("marc:datafield")
    ## #
    ##     out.openTag("marc:datafield",[["tag","520"],["ind1"," "],["ind2"," "]])
    ##     out.writeTag("marc:subfield",session.getDescription(),[["code","a"]])
    ##     out.closeTag("marc:datafield")

    ##     out.openTag("marc:datafield",[["tag","611"],["ind1","2"],["ind2","4"]])
    ##     out.writeTag("marc:subfield",session.getConference().getTitle(),[["code","a"]])
    ##     out.closeTag("marc:datafield")
    ##     out.openTag("marc:datafield",[["tag","650"],["ind1","1"],["ind2","7"]])
    ##     out.writeTag("marc:subfield","SzGeCERN",[["code","2"]])
    ##     out.closeTag("marc:datafield")


    ##     # tag 100/700 Convener name
    ##     cList = session.getConvenerList()

    ##     for user in cList:
    ##         if user == cList[0]:
    ##             code = "100"
    ##         else:
    ##             code = "700"
    ##         out.openTag("marc:datafield",[["tag",code],["ind1"," "],["ind2"," "]])
    ##         fullName = user.getFamilyName() + " " + user.getFirstName()
    ##         out.writeTag("marc:subfield",fullName,[["code","a"]])
    ##         out.writeTag("marc:subfield","Convener",[["code","e"]])
    ##         out.writeTag("marc:subfield",user.getAffiliation(),[["code","u"]])
    ##         out.closeTag("marc:datafield")

    ##     matList = session.getAllMaterialList()
    ##     for mat in matList:
    ##         if mat.canView(self.__aw):
    ##             if includeMaterial:
    ##                 self.materialToXMLMarc21(mat, out=out)

    ##     out.openTag("marc:datafield",[["tag","962"],["ind1"," "],["ind2"," "]])
    ##     out.writeTag("marc:subfield","INDICO.%s"%self.dataInt.objToId(session.getConference()),[["code","b"]])
    ##     out.closeTag("marc:datafield")

    ##     out.openTag("marc:datafield",[["tag","970"],["ind1"," "],["ind2"," "]])
    ##     confses = "INDICO." + self.dataInt.objToId(session.getConference(), separator=".")
    ##     out.writeTag("marc:subfield",confses,[["code","a"]])
    ##     out.closeTag("marc:datafield")

    ##     out.openTag("marc:datafield",[["tag","980"],["ind1"," "],["ind2"," "]])
    ##     confcont = "INDICO." + self.dataInt.objToId(session.getConference())
    ##     out.writeTag("marc:subfield",confcont,[["code","a"]])
    ##     out.closeTag("marc:datafield")

    ##     out.openTag("marc:datafield",[["tag","856"],["ind1","4"],["ind2"," "]])
    ##     url = str(urlHandlers.UHSessionDisplay.getURL(session))
    ##     out.writeTag("marc:subfield",url,[["code","u"]])
    ##     out.writeTag("marc:subfield", "Session details", [["code","y"]])
    ##     out.closeTag("marc:datafield")


    #fb

    def contribToXMLMarc21(self,cont,includeMaterial=1, out=None, forceCache=False):
        if not out:
            out = self._XMLGen
        #try to get a cache
        version = "MARC21_mat-%s"%(includeMaterial)
        obj = None
        if not forceCache:
            obj = self.cache.loadObject(version, cont)
        if obj:
            xml = obj.getContent()
        else:
            # No cache, build the XML
            temp = XMLGen(init=False)
            self._contribToXMLMarc21(cont,includeMaterial, out=temp)
            xml = temp.getXml()
            # save XML in cache
            self.cache.cacheObject(version, xml, cont)
        out.writeXML(xml)


    def _contribToXMLMarc21(self,cont,includeMaterial=1, out=None):
        if not out:
            out = self._XMLGen

        #out.writeTag("controlfield","SzGeCERN",[["tag","003"]])
        out.writeTag("marc:leader", "00000nmm  2200000uu 4500")
        out.openTag("marc:datafield",[["tag","035"],["ind1"," "],["ind2"," "]])
        out.writeTag("marc:subfield","INDICO.%s"%self.dataInt.objToId(cont, separator="."),[["code","a"]])
        out.closeTag("marc:datafield")
    #
        out.openTag("marc:datafield",[["tag","035"],["ind1"," "],["ind2"," "]])
        out.writeTag("marc:subfield",self.dataInt.objToId(cont, separator="t"),[["code","a"]])
        out.writeTag("marc:subfield","Indico",[["code","9"]])
        out.closeTag("marc:datafield")

        out.openTag("marc:datafield",[["tag","245"],["ind1"," "],["ind2"," "]])
        out.writeTag("marc:subfield",cont.getTitle(),[["code","a"]])
        out.closeTag("marc:datafield")

        out.openTag("marc:datafield",[["tag","300"],["ind1"," "],["ind2"," "]])
        out.writeTag("marc:subfield",cont.getDuration(),[["code","a"]])
        out.closeTag("marc:datafield")

        out.openTag("marc:datafield",[["tag","111"],["ind1"," "],["ind2"," "]])
        out.writeTag("marc:subfield", self.dataInt.objToId(cont.getConference()),[["code","g"]])
        out.closeTag("marc:datafield")

        for path in cont.getConference().getCategoriesPath():
            out.openTag("marc:datafield",[["tag","650"],["ind1"," "],["ind2","7"]])
            out.writeTag("marc:subfield", ":".join(path), [["code","a"]])
            out.closeTag("marc:datafield")

        l=cont.getLocation()
        if (l and l.getName() != "") or cont.getStartDate() is not None:
            out.openTag("marc:datafield",[["tag","518"],["ind1"," "],["ind2"," "]])
            if l:
                if l.getName() != "":
                    out.writeTag("marc:subfield",l.getName(),[["code","r"]])
            if cont.getStartDate() is not None:
                out.writeTag("marc:subfield","%d-%s-%sT%s:%s:00Z" %(cont.getStartDate().year, string.zfill(cont.getStartDate().month,2), string.zfill(cont.getStartDate().day,2), string.zfill(cont.getStartDate().hour,2), string.zfill(cont.getStartDate().minute,2)),[["code","d"]])
                out.writeTag("marc:subfield","%d-%s-%sT%s:%s:00Z" %(cont.getEndDate().year, string.zfill(cont.getEndDate().month,2), string.zfill(cont.getEndDate().day,2), string.zfill(cont.getEndDate().hour,2), string.zfill(cont.getEndDate().minute,2)),[["code","h"]])
            out.closeTag("marc:datafield")
    #
        out.openTag("marc:datafield",[["tag","520"],["ind1"," "],["ind2"," "]])
        out.writeTag("marc:subfield",cont.getDescription(),[["code","a"]])
        out.closeTag("marc:datafield")

        out.openTag("marc:datafield",[["tag","611"],["ind1","2"],["ind2","4"]])
        out.writeTag("marc:subfield",cont.getConference().getTitle(),[["code","a"]])
        out.closeTag("marc:datafield")


        if cont.getReportNumberHolder().listReportNumbers():
            out.openTag("marc:datafield",[["tag","088"],["ind1"," "],["ind2"," "]])
            for report in cont.getReportNumberHolder().listReportNumbers():
                out.writeTag("marc:subfield",report[1],[["code","a"]])
            out.closeTag("marc:datafield")


        out.openTag("marc:datafield",[["tag","653"],["ind1","1"],["ind2"," "]])
        keywords = cont.getKeywords()
        keywords.replace("\r\n", "\n")
        for keyword in keywords.split("\n"):
            out.writeTag("marc:subfield",keyword,[["code","a"]])
        out.closeTag("marc:datafield")


    #
        out.openTag("marc:datafield",[["tag","650"],["ind1","1"],["ind2","7"]])
        out.writeTag("marc:subfield","SzGeCERN",[["code","2"]])
        if cont.getTrack():
            out.writeTag("marc:subfield",cont.getTrack().getTitle(),[["code","a"]])
        out.closeTag("marc:datafield")


        # tag 700 Speaker name
        aList = cont.getAuthorList()
        sList = cont.getSpeakerList()
        list = {}
        auth = cont.getPrimaryAuthorList()
        if auth:
            auth = auth[0]
            list[auth] = ["Primary Author"]
        for user in aList:
            if user in list:
                if user != auth:
                    list[user].append("Author")
            else:
                list[user] = ["Author"]

        for user in sList:
            if user in list:
                list[user].append("Speaker")
            else:
                list[user] = ["Speaker"]

        if auth:
            user = auth
            out.openTag("marc:datafield",[["tag","100"],["ind1"," "],["ind2"," "]])
            fullName = auth.getFamilyName() + " " + auth.getFirstName()
            out.writeTag("marc:subfield",fullName,[["code","a"]])
            for val in list[user]:
                out.writeTag("marc:subfield",val,[["code","e"]])
            out.writeTag("marc:subfield",auth.getAffiliation(),[["code","u"]])
            out.closeTag("marc:datafield")
            del list[auth]

        for user in list.keys():
            out.openTag("marc:datafield",[["tag","700"],["ind1"," "],["ind2"," "]])
            fullName = user.getFamilyName() + " " + user.getFirstName()
            out.writeTag("marc:subfield",fullName,[["code","a"]])
            for val in list[user]:
                out.writeTag("marc:subfield",val,[["code","e"]])
            out.writeTag("marc:subfield",user.getAffiliation(),[["code","u"]])
            out.closeTag("marc:datafield")





        matList = cont.getAllMaterialList()
        for mat in matList:
            #out.openTag("datafield",[["tag","856"],["ind1","4"],["ind2"," "]])
            if self.dataInt.isPrivateDataInt() or mat.canView(self.__aw):
                if includeMaterial:
                    self.materialToXMLMarc21(mat, out=out)
            #   else:
            #       out.writeTag("material",out.writeTag("id",mat.id))
        # no subContibution
        #for subC in cont.getSubContributionList():
        #    self.subContributionToXML(subC,includeMaterial)
            #out.closeTag("datafield")



        out.openTag("marc:datafield",[["tag","962"],["ind1"," "],["ind2"," "]])
        out.writeTag("marc:subfield","INDICO.%s"%self.dataInt.objToId(cont.getConference()),[["code","b"]])
        out.closeTag("marc:datafield")

        out.openTag("marc:datafield",[["tag","970"],["ind1"," "],["ind2"," "]])
        confcont = "INDICO." + self.dataInt.objToId(cont, separator=".")
        out.writeTag("marc:subfield",confcont,[["code","a"]])
        out.closeTag("marc:datafield")

        out.openTag("marc:datafield",[["tag","980"],["ind1"," "],["ind2"," "]])
        confcont = "INDICO." + self.dataInt.objToId(cont.getConference())
        out.writeTag("marc:subfield",confcont,[["code","a"]])
        out.closeTag("marc:datafield")

        out.openTag("marc:datafield",[["tag","856"],["ind1","4"],["ind2"," "]])
        url = str(urlHandlers.UHContributionDisplay.getURL(cont))
        out.writeTag("marc:subfield",url,[["code","u"]])
        out.writeTag("marc:subfield", "Contribution details", [["code","y"]])
        out.closeTag("marc:datafield")

    ####
    #fb


    def subContribToXMLMarc21(self,subCont,includeMaterial=1, out=None, forceCache=False):
        if not out:
            out = self._XMLGen
        #try to get a cache
        version = "MARC21_mat-%s"%(includeMaterial)
        obj = None
        if not forceCache:
            obj = self.cache.loadObject(version, subCont)
        if obj:
            xml = obj.getContent()
        else:
            # No cache, build the XML
            temp = XMLGen(init=False)
            self._subContribToXMLMarc21(subCont,includeMaterial, out=temp)
            xml = temp.getXml()
            # save XML in cache
            self.cache.cacheObject(version, xml, subCont)
        out.writeXML(xml)


    def _subContribToXMLMarc21(self,subCont,includeMaterial=1, out=None):
        if not out:
            out = self._XMLGen

        #out.writeTag("controlfield","SzGeCERN",[["tag","003"]])
        out.writeTag("marc:leader", "00000nmm  2200000uu 4500")
        out.openTag("marc:datafield",[["tag","035"],["ind1"," "],["ind2"," "]])
        out.writeTag("marc:subfield","INDICO.%s"%(self.dataInt.objToId(subCont, separator=".")),[["code","a"]])
        out.closeTag("marc:datafield")
    #
        out.openTag("marc:datafield",[["tag","035"],["ind1"," "],["ind2"," "]])
        out.writeTag("marc:subfield",self.dataInt.objToId(subCont, separator=["t","sc"]),[["code","a"]])
        out.writeTag("marc:subfield","Indico",[["code","9"]])
        out.closeTag("marc:datafield")

        out.openTag("marc:datafield",[["tag","245"],["ind1"," "],["ind2"," "]])
        out.writeTag("marc:subfield",subCont.getTitle(),[["code","a"]])
        out.closeTag("marc:datafield")

        out.openTag("marc:datafield",[["tag","300"],["ind1"," "],["ind2"," "]])
        out.writeTag("marc:subfield",subCont.getDuration(),[["code","a"]])
        out.closeTag("marc:datafield")

        out.openTag("marc:datafield",[["tag","111"],["ind1"," "],["ind2"," "]])
        out.writeTag("marc:subfield", self.dataInt.objToId(subCont.getConference(), separator="."),[["code","g"]])
        out.closeTag("marc:datafield")

        if subCont.getReportNumberHolder().listReportNumbers():
            out.openTag("marc:datafield",[["tag","088"],["ind1"," "],["ind2"," "]])
            for report in subCont.getReportNumberHolder().listReportNumbers():
                out.writeTag("marc:subfield",report[1],[["code","a"]])
            out.closeTag("marc:datafield")


        out.openTag("marc:datafield",[["tag","653"],["ind1","1"],["ind2"," "]])
        keywords = subCont.getKeywords()
        keywords.replace("\r\n", "\n")
        for keyword in keywords.split("\n"):
            out.writeTag("marc:subfield",keyword,[["code","a"]])
        out.closeTag("marc:datafield")


        for path in subCont.getConference().getCategoriesPath():
            out.openTag("marc:datafield",[["tag","650"],["ind1"," "],["ind2","7"]])
            out.writeTag("marc:subfield", ":".join(path), [["code","a"]])
            out.closeTag("marc:datafield")

        l=subCont.getLocation()
        if (l and l.getName() != "") or subCont.getContribution().getStartDate() is not None:
            out.openTag("marc:datafield",[["tag","518"],["ind1"," "],["ind2"," "]])
            if l:
                if l.getName() != "":
                    out.writeTag("marc:subfield",l.getName(),[["code","r"]])
            if subCont.getContribution().getStartDate() is not None:
                out.writeTag("marc:subfield","%d-%s-%sT%s:%s:00Z" %(subCont.getContribution().getStartDate().year, string.zfill(subCont.getContribution().getStartDate().month,2), string.zfill(subCont.getContribution().getStartDate().day,2), string.zfill(subCont.getContribution().getStartDate().hour,2), string.zfill(subCont.getContribution().getStartDate().minute,2)),[["code","d"]])
                #out.writeTag("subfield","%d-%s-%sT%s:%s:00Z" %(subCont.getEndDate().year, string.zfill(subCont.getEndDate().month,2), string.zfill(subCont.getEndDate().day,2), string.zfill(subCont.getEndDate().hour,2), string.zfill(subCont.getEndDate().minute,2)),[["code","h"]])
            out.closeTag("marc:datafield")
    #
        out.openTag("marc:datafield",[["tag","520"],["ind1"," "],["ind2"," "]])
        out.writeTag("marc:subfield",subCont.getDescription(),[["code","a"]])
        out.closeTag("marc:datafield")

        out.openTag("marc:datafield",[["tag","611"],["ind1","2"],["ind2","4"]])
        out.writeTag("marc:subfield",subCont.getConference().getTitle(),[["code","a"]])
        out.closeTag("marc:datafield")
    #
        out.openTag("marc:datafield",[["tag","650"],["ind1","1"],["ind2","7"]])
        out.writeTag("marc:subfield","SzGeCERN",[["code","2"]])
        if subCont.getContribution().getTrack():
            out.writeTag("marc:subfield",subCont.getContribution().getTrack().getTitle(),[["code","a"]])
        out.closeTag("marc:datafield")


        # tag 700 Speaker name
        aList = subCont.getContribution().getAuthorList()
        sList = subCont.getSpeakerList()
        list = {}
        auth = subCont.getContribution().getPrimaryAuthorList()
        if auth:
            auth = auth[0]
            list[auth] = ["Primary Author"]
        for user in aList:
            if user in list:
                if user != auth:
                    list[user].append("Author")
            else:
                list[user] = ["Author"]

        for user in sList:
            if user in list:
                list[user].append("Speaker")
            else:
                list[user] = ["Speaker"]

        if auth:
            user = auth
            out.openTag("marc:datafield",[["tag","100"],["ind1"," "],["ind2"," "]])
            fullName = auth.getFamilyName() + " " + auth.getFirstName()
            out.writeTag("marc:subfield",fullName,[["code","a"]])
            for val in list[user]:
                out.writeTag("marc:subfield",val,[["code","e"]])
            out.writeTag("marc:subfield",auth.getAffiliation(),[["code","u"]])
            out.closeTag("marc:datafield")
            del list[auth]

        for user in list.keys():
            out.openTag("marc:datafield",[["tag","700"],["ind1"," "],["ind2"," "]])
            fullName = user.getFamilyName() + " " + user.getFirstName()
            out.writeTag("marc:subfield",fullName,[["code","a"]])
            for val in list[user]:
                out.writeTag("marc:subfield",val,[["code","e"]])
            out.writeTag("marc:subfield",user.getAffiliation(),[["code","u"]])
            out.closeTag("marc:datafield")





        matList = subCont.getAllMaterialList()
        for mat in matList:
            #out.openTag("datafield",[["tag","856"],["ind1","4"],["ind2"," "]])
            if self.dataInt.isPrivateDataInt() or mat.canView(self.__aw):
                if includeMaterial:
                    self.materialToXMLMarc21(mat, out=out)
            #    else:
            #        out.writeTag("material",out.writeTag("id",mat.id))




        out.openTag("marc:datafield",[["tag","962"],["ind1"," "],["ind2"," "]])
        out.writeTag("marc:subfield","INDICO.%s"%self.dataInt.objToId(subCont.getConference()),[["code","b"]])
        out.closeTag("marc:datafield")

        out.openTag("marc:datafield",[["tag","970"],["ind1"," "],["ind2"," "]])
        confcont = "INDICO." + self.dataInt.objToId(subCont, separator=".")
        out.writeTag("marc:subfield",confcont,[["code","a"]])
        out.closeTag("marc:datafield")

        out.openTag("marc:datafield",[["tag","980"],["ind1"," "],["ind2"," "]])
        confcont = "INDICO." + self.dataInt.objToId(subCont.getConference())
        out.writeTag("marc:subfield",confcont,[["code","a"]])
        out.closeTag("marc:datafield")

        out.openTag("marc:datafield",[["tag","856"],["ind1","4"],["ind2"," "]])
        url = str(urlHandlers.UHSubContributionDisplay.getURL(subCont))
        out.writeTag("marc:subfield",url,[["code","u"]])
        out.writeTag("marc:subfield", "Contribution details", [["code","y"]])
        out.closeTag("marc:datafield")


    def materialToXMLMarc21(self,mat, out=None):
        if not out:
            out = self._XMLGen
        #out.openTag("material")
        #out.writeTag("ID",mat.getId())
        #out.writeTag("title",mat.title)
        #out.writeTag("description",mat.description)
        #out.writeTag("type",mat.type)
        rList = mat.getResourceList()
        self.resourcesToXMLMarc21(rList, out=out)
        #out.closeTag("material")

    def resourcesToXMLMarc21(self, rList, out=None):
        if not out:
            out = self._XMLGen
        #out.openTag("resources")
        for res in rList:
            if self.dataInt.isPrivateDataInt() or res.canView(self.__aw):
                self.resourceToXMLMarc21(res, out=out)
        #out.closeTag("resources")



    def resourceToXMLMarc21(self,res, out=None):
        if not out:
            out = self._XMLGen
        if type(res) == conference.LocalFile:
            self.resourceFileToXMLMarc21(res, out=out)
        else:
            self.resourceLinkToXMLMarc21(res, out=out)

    def resourceLinkToXMLMarc21(self,res, out=None):
        if not out:
            out = self._XMLGen

        #out.writeTag("name",res.getName())
        out.openTag("marc:datafield",[["tag","856"],["ind1","4"],["ind2"," "]])
        out.writeTag("marc:subfield",res.getDescription(),[["code","a"]])
        #out.writeTag("description",res.getDescription())
        #out.writeTag("url",res.getURL())
        out.writeTag("marc:subfield",res.getURL(),[["code","u"]])
        out.writeTag("marc:subfield", "resource", [["code","x"]])
        out.writeTag("marc:subfield", res.getOwner().getTitle(), [["code","y"]])
        out.closeTag("marc:datafield")

    def resourceFileToXMLMarc21(self,res, out=None):
        if not out:
            out = self._XMLGen

        #out.writeTag("name",res.getName())
        #out.writeTag("description",res.getDescription())
        #out.writeTag("type",res.fileType)
        out.openTag("marc:datafield",[["tag","856"],["ind1","4"],["ind2"," "]])
        out.writeTag("marc:subfield",res.getDescription(),[["code","a"]])
        try:
            out.writeTag("marc:subfield",res.getSize(),[["code","s"]])
        except:
            pass
        #out.writeTag("subfield",res.getURL(),[["code","u"]])

        #out.writeTag("subfield",res.getFileName(),[["code","q"]])
        url = str(urlHandlers.UHFileAccess.getURL( res ))
        out.writeTag("marc:subfield",url,[["code","u"]])
        out.writeTag("marc:subfield", res.getFileName(), [["code","y"]])
        out.writeTag("marc:subfield", "resource", [["code","x"]])
        out.closeTag("marc:datafield")
        #out.writeTag("duration","1")#TODO:DURATION ISN'T ESTABLISHED
        #cDate = res.getCreationDate()
        #creationDateStr = "%d-%s-%sT%s:%s:00Z" %(cDate.year, string.zfill(cDate.month,2), string.zfill(cDate.day,2), string.zfill(cDate.hour,2), string.zfill(cDate.minute,2))
        #out.writeTag("creationDate",creationDateStr)

class XMLCacheEntry(MultiLevelCacheEntry):
    def __init__(self, objId):
        MultiLevelCacheEntry.__init__(self)
        self.id = objId

    def getId(self):
        return self.id

    @classmethod
    def create(cls, content, obj):
        entry = cls(getHierarchicalId(obj))
        entry.setContent(content)
        return entry


class XMLCache(MultiLevelCache):

    _entryFactory = XMLCacheEntry

    def __init__(self):
        MultiLevelCache.__init__(self, 'xml')


    def isDirty(self, file, object):

        # get event OAI date
        oaiModDate = resolveHierarchicalId(object.getId()).getOAIModificationDate()
        fileModDate = timezone("UTC").localize(
            datetime.utcfromtimestamp(os.path.getmtime(file)))

        # check file system date vs. event date
        return (oaiModDate > fileModDate)

    def _generatePath(self, entry):
        """
        Generate the actual hierarchical location
        """

        # by default, use the dots and first char
        # a205.0 -> /cachedir/a/a205/0

        tree = entry.getId().split('.')
        return [tree[0][0]]+tree


class ProtectedXMLCache(XMLCache):
    """
    XMLCache that is content protection-aware
    It uses a DataInt, in order to map object to their
    corresponding ids (rXXX, pXXX)
    """


    def __init__(self, dataInt):
        XMLCache.__init__(self)
        self.dataInt = dataInt

    def _getRecordId(self, obj):
        return self.dataInt.objToId(obj, separator='.')

    def generatePath(self, obj):
        """
        Generate the actual hierarchical location
        """

        # by default, use the dots and first char
        # pa205.0 -> /cachedir/p/a/a205/0

        tree = self._getRecordId(obj).split('.')
        return [tree[0][0]]+[tree[0][1]]+[tree[0][1:]]+tree[1:]
