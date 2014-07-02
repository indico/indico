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

from datetime import datetime
from flask import request
from hashlib import md5
from pytz import timezone

import string
from indico.util.json import dumps
import StringIO

from lxml import etree

import MaKaC.conference as conference
import MaKaC.schedule as schedule
import MaKaC.webcast as webcast
import MaKaC.webinterface.urlHandlers as urlHandlers
from MaKaC.webinterface.linking import RoomLinker
from Configuration import Config
from xmlGen import XMLGen
import os
from math import ceil
from MaKaC.i18n import _
from MaKaC.common.timezoneUtils import DisplayTZ
from MaKaC.common.utils import getHierarchicalId, resolveHierarchicalId
from MaKaC.common.cache import MultiLevelCache, MultiLevelCacheEntry
from MaKaC.rb_location import CrossLocationQueries, CrossLocationDB
from MaKaC.plugins.base import Observable
from MaKaC.user import Avatar, Group
from MaKaC.common.TemplateExec import escapeHTMLForJS

from indico.util.event import uniqueId


# TODO This really needs to be fixed... no i18n and strange implementation using month names as keys
def stringToDate( str ):
    months = { "January":1, "February":2, "March":3, "April":4, "May":5, "June":6, "July":7, "August":8, "September":9, "October":10, "November":11, "December":12 }
    [ day, month, year ] = str.split("-")
    return datetime(int(year),months[month],int(day))


class XSLTransformer:

    def __init__(self, stylesheet):
        # instanciate stylesheet object
        styledoc = etree.parse(stylesheet)
        self.__style = etree.XSLT(styledoc)

    def process (self, xml):

        doc = etree.parse(StringIO.StringIO(xml))
        # compute the transformation
        result = self.__style(doc)

        return str(result)

class outputGenerator(Observable):
    """
    this class generates the application standard XML (getBasicXML)
    and also provides a method to format it using an XSLt stylesheet
    (getFormattedOutput method)
    """

    def __init__(self, aw, XG = None):
        self.__aw = aw
        if XG != None:
            self._XMLGen = XG
        else:
            self._XMLGen = XMLGen()
        self._config = Config.getInstance()
        self.text = ""
        self.time_XML = 0
        self.time_HTML = 0
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

    def _getRecordCollection(self, obj):
        if obj.hasAnyProtection():
            return "INDICOSEARCH.PRIVATE"
        else:
            return "INDICOSEARCH.PUBLIC"

    def getOutput(self, conf, stylesheet, vars=None, includeSession=1, includeContribution=1, includeSubContribution=1, includeMaterial=1, showSession="all", showDate="all", showContribution="all"):
        # get xml conference
        xml = self._getBasicXML(conf, vars, includeSession,includeContribution,includeSubContribution,includeMaterial,showSession,showDate,showContribution)
        if not os.path.exists(stylesheet):
            self.text = _("Cannot find stylesheet")
        if os.path.basename(stylesheet) == "xml.xsl":
            self.text = xml
        else:
            # instanciate the XSL tool
            parser = XSLTransformer(stylesheet)
            self.text = parser.process(xml)
        return self.text


    def getFormattedOutput(self, rh, conf, stylesheet, vars=None, includeSession=1,includeContribution=1,includeSubContribution=1,includeMaterial=1,showSession="all",showDate="all",showContribution="all"):
        """
        conf: conference object
        stylesheet: path to the xsl file
        """
        self.getOutput(conf, stylesheet, vars, includeSession, includeContribution, includeSubContribution, includeMaterial, showSession, showDate, showContribution)
        html = self.text
        if request.is_secure:
            imagesBaseURL = Config.getInstance().getImagesBaseURL()
            imagesBaseSecureURL = urlHandlers.setSSLPort(Config.getInstance().getImagesBaseSecureURL())
            baseURL = Config.getInstance().getBaseURL()
            baseSecureURL = urlHandlers.setSSLPort(Config.getInstance().getBaseSecureURL())
            html = html.replace(imagesBaseURL, imagesBaseSecureURL)
            html = html.replace(escapeHTMLForJS(imagesBaseURL), escapeHTMLForJS(imagesBaseSecureURL))
            html = html.replace(baseURL, baseSecureURL)
            html = html.replace(escapeHTMLForJS(baseURL), escapeHTMLForJS(baseSecureURL))
        return html

    def _getBasicXML(self, conf, vars, includeSession, includeContribution, includeSubContribution, includeMaterial, showSession="all", showDate="all", showContribution="all", showSubContribution="all", out=None):
        """
        conf: conference object
        """
        if not out:
            out = self._XMLGen
        #out.initXml()
        out.openTag("iconf")
        self._confToXML(conf, vars, includeSession, includeContribution, includeSubContribution, includeMaterial, showSession, showDate, showContribution, out=out)
        out.closeTag("iconf")
        return out.getXml()

    def _userToXML(self, obj, user, out):
        out.openTag("user")
        out.writeTag("title", user.getTitle())
        out.writeTag("name", "", [["first", user.getFirstName()], ["middle", ""], ["last", user.getFamilyName()]])
        out.writeTag("organization", user.getAffiliation())

        if obj.canModify(self.__aw):
            out.writeTag("email", user.getEmail())

        out.writeTag("emailHash", md5(user.getEmail()).hexdigest())

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

    def _getExternalUserAccounts(self, user):
        accounts = []
        for identity in user.getIdentityList(create_identities=True):
            if identity.getAuthenticatorTag() != 'Local':
                accounts.append(identity.getLogin())

        return accounts

    def _generateLinkField(self, url, obj, text, out):
        out.openTag("datafield", [["tag", "856"], ["ind1", "4"], ["ind2", " "]])
        out.writeTag("subfield", str(url.getURL(obj)), [["code", "u"]])
        out.writeTag("subfield", text, [["code", "y"]])
        out.closeTag("datafield")

    def _generateACLDatafield(self, eType, memberList, objId, out):
        """
        Generates a specific MARCXML 506 field containing the ACL
        """
        if eType:
            out.openTag("datafield", [["tag", "506"],
                                      ["ind1", "1"], ["ind2", " "]])
            for memberId in memberList:
                out.writeTag("subfield", memberId, [["code", "d"]])
            out.writeTag("subfield", eType, [["code", "f"]])

        else:
            out.openTag("datafield", [["tag", "506"], ["ind1", "0"],
                                      ["ind2", " "]])

        # define which part of the record the list concerns
        if objId != None:
            out.writeTag("subfield", "INDICO.%s" % \
                         objId, [["code", "3"]])

        out.closeTag("datafield")

    def _generateAccessList(self, obj, out, specifyId=True):
        """
        Generate a comprehensive access list showing all users and e-groups who
        may access this object, taking into account the permissions and access
        lists of its owners.
        obj could be a Conference, Session, Contribution, Material, Resource
        or SubContribution object.
        """

        allowed_users = obj.getRecursiveAllowedToAccessList()

        # Populate two lists holding email/group strings instead of
        # Avatar/Group objects
        allowed_logins = []
        allowed_groups = []

        objId = uniqueId(obj) if specifyId else None

        for user_obj in allowed_users:
            if isinstance(user_obj, Avatar):
                for account in self._getExternalUserAccounts(user_obj):
                    allowed_logins.append(account)
            elif isinstance(user_obj, Group) and user_obj.groupType != "Default":
                allowed_groups.append(user_obj.getId())
            else:
                allowed_logins.append(user_obj.getId())

        if len(allowed_groups) + len(allowed_logins) > 0:
            # Create XML list of groups
            if len(allowed_groups) > 0:
                self._generateACLDatafield('group', allowed_groups, objId, out)

            # Create XML list of emails
            if len(allowed_logins) > 0:
                self._generateACLDatafield('username', allowed_logins, objId, out)
        else:
            # public record
            self._generateACLDatafield(None, None, objId, out)

    def _confToXML(self,
                   conf,
                   vars,
                   includeSession         = 1,
                   includeContribution    = 1,
                   includeSubContribution = 1,
                   includeMaterial        = 1,
                   showSession            = "all",
                   showDate               = "all",
                   showContribution       = "all",
                   showSubContribution    = "all",
                   showWithdrawed         = True,
                   useSchedule            = True,
                   out                    = None,
                   recordingManagerTags   = None):

        if not out:
            out = self._XMLGen
        if vars and vars.has_key("frame") and vars["frame"] == "no":
            modificons = 0
        else:
            modificons = 1

        out.writeTag("ID", conf.getId())

        if conf.getOwnerList():
            out.writeTag("category", conf.getOwnerList()[0].getName())
        else:
            out.writeTag("category", "")

        out.writeTag("parentProtection", dumps(conf.getAccessController().isProtected()))
        out.writeTag("materialList", dumps(self._generateMaterialList(conf)))

        self._notify('addXMLMetadata', {'out': out, 'obj': conf, 'type':"conference", 'recordingManagerTags':recordingManagerTags})

        if conf.canModify(self.__aw) and vars and modificons:
            out.writeTag("modifyLink", vars["modifyURL"])
        if conf.canModify( self.__aw ) and vars and modificons:
            out.writeTag("minutesLink", True)
        if conf.canModify( self.__aw ) and vars and modificons:
            out.writeTag("materialLink", True)
        if conf.canModify( self.__aw ) and vars and vars.has_key("cloneURL") and modificons:
            out.writeTag("cloneLink", vars["cloneURL"])
        if  vars and vars.has_key("iCalURL"):
            out.writeTag("iCalLink", vars["iCalURL"])
        if  vars and vars.has_key("webcastAdminURL"):
            out.writeTag("webcastAdminLink", vars["webcastAdminURL"])

        if conf.getOrgText() != "":
            out.writeTag("organiser", conf.getOrgText())

        out.openTag("announcer")
        chair = conf.getCreator()
        if chair != None:
            self._userToXML(conf, chair, out)
        out.closeTag("announcer")

        sinfo = conf.getSupportInfo()

        if sinfo.getEmail() != '':
            out.writeTag("supportEmail", sinfo.getEmail(), [["caption", sinfo.getCaption()]])

        keywords = conf.getKeywords()
        keywords = keywords.replace("\r\n", "\n")
        keywordsList = filter (lambda a: a != '', keywords.split("\n"))
        if keywordsList:
            out.openTag("keywords")
            for keyword in keywordsList:
                out.writeTag("keyword",keyword.strip())
            out.closeTag("keywords")

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

        evaluation = conf.getEvaluation()
        if evaluation.isVisible() and evaluation.inEvaluationPeriod() and evaluation.getNbOfQuestions()>0 :
            out.writeTag("evaluationLink",urlHandlers.UHConfEvaluationDisplay.getURL(conf))

        out.writeTag("closed", str(conf.isClosed()))

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
                self._userToXML(conf, chair, out)
            if conf.getChairmanText() != "":
                out.writeTag("UnformatedUser",conf.getChairmanText())
            out.closeTag("chair")


        # Keep track of days that have some slots that will be displayed
        nonEmptyDays = set()

        # This case happens when called by RecordingManager to generate XML for a contribution:
        if showContribution != "all" and conf.getContributionById(showContribution) != None:
            self._contribToXML(conf.getContributionById(showContribution),vars,includeSubContribution,includeMaterial,conf, showSubContribution=showSubContribution,out=out, recordingManagerTags=recordingManagerTags)
        elif useSchedule:
            confSchedule = conf.getSchedule()
            if showDate == "all":
                entrylist = confSchedule.getEntries()
            else:
                entrylist = confSchedule.getEntriesOnDay(timezone(tz).localize(stringToDate(showDate)))
            for entry in entrylist:
                if type(entry) is schedule.BreakTimeSchEntry: #TODO: schedule.BreakTimeSchEntry doesn't seem to exist!
                    self._breakToXML(entry, out=out)
                    nonEmptyDays.add(entry.getStartDate().date())
                elif type(entry) is conference.ContribSchEntry:
                    owner = entry.getOwner()
                    if owner.canView(self.__aw):
                        if includeContribution:
                            if showWithdrawed or not isinstance(owner.getCurrentStatus(), conference.ContribStatusWithdrawn):
                                self._contribToXML(owner,vars,includeSubContribution,includeMaterial,conf, showSubContribution=showSubContribution,out=out)
                                nonEmptyDays.add(owner.getStartDate().date())
                elif type(entry) is schedule.LinkedTimeSchEntry: #TODO: schedule.LinkedTimeSchEntry doesn't seem to exist!
                    owner = entry.getOwner()
                    if type(owner) is conference.Contribution:
                        if owner.canView(self.__aw):
                            if includeContribution:
                                if showWithdrawed or not isinstance(owner.getCurrentStatus(), conference.ContribStatusWithdrawn):
                                    self._contribToXML(owner,vars,includeSubContribution,includeMaterial,conf, out=out)
                                    nonEmptyDays.add(owner.getStartDate().date())
                    elif type(owner) is conference.Session:
                        if owner.canView(self.__aw):
                            if includeSession and (showSession == "all" or owner.getId() == showSession):
                                self._sessionToXML(owner,vars,includeContribution,includeMaterial, showWithdrawed=showWithdrawed, out=out, recordingManagerTags=recordingManagerTags)
                                nonEmptyDays.add(owner.getStartDate().date())
                    elif type(owner) is conference.SessionSlot:
                        if owner.getSession().canView(self.__aw):
                            if includeSession and (showSession == "all" or owner.getSession().getId() == showSession):
                                self._slotToXML(owner,vars,includeContribution,includeMaterial, showWithdrawed=showWithdrawed, out=out, recordingManagerTags=recordingManagerTags)
                                nonEmptyDays.add(owner.getStartDate().date())
        else:
            confSchedule = conf.getSchedule()
            for entry in confSchedule.getEntries():
                if type(entry) is conference.ContribSchEntry:
                    owner = entry.getOwner()
                    if owner.canView(self.__aw):
                        if includeContribution:
                            self._contribToXML(owner,vars,includeSubContribution,includeMaterial,conf,showSubContribution=showSubContribution,out=out, recordingManagerTags=recordingManagerTags)
                            nonEmptyDays.add(owner.getStartDate().date())
            sessionList = conf.getSessionList()
            for session in sessionList: # here is the part that displays all the sessions (for the RecordingManager, anyway). It should be changed to check if showSession has been set.
                if session.canAccess(self.__aw) and includeSession and (showSession == 'all' or str(session.getId()) == str(showSession)):
                    self._sessionToXML(session, vars, includeContribution, includeMaterial, showWithdrawed=showWithdrawed, useSchedule=False, out=out, recordingManagerTags=recordingManagerTags)
                    nonEmptyDays.add(session.getStartDate().date())

        nonEmptyDays = list(nonEmptyDays)
        nonEmptyDays.sort()

        if vars:
            daysPerRow = vars.get("daysPerRow", None)
            firstDay = vars.get("firstDay", None)
            lastDay = vars.get("lastDay", None)

            if daysPerRow or firstDay or lastDay:
                if firstDay:
                    firstDay = timezone(tz).localize(stringToDate(firstDay)).date()
                    nonEmptyDays = filter(lambda day: day >= firstDay, nonEmptyDays)

                if lastDay:
                    lastDay = timezone(tz).localize(stringToDate(lastDay)).date()
                    nonEmptyDays = filter(lambda day: day <= lastDay, nonEmptyDays)

                if daysPerRow:
                    daysPerRow = int(daysPerRow)

                if not daysPerRow or daysPerRow > len(nonEmptyDays):
                    daysPerRow = len(nonEmptyDays)

                if daysPerRow > 0:
                    numOfRows = int(ceil(len(nonEmptyDays) / float(daysPerRow)))
                    for row in range(0, numOfRows):
                        fromDate = nonEmptyDays[row * daysPerRow]
                        toIndex = (row + 1) * daysPerRow - 1
                        if toIndex >= len(nonEmptyDays):
                            toIndex = len(nonEmptyDays) - 1
                        toDate = nonEmptyDays[toIndex]
                        out.openTag("line")
                        out.writeTag("fromDate", "%d%s%s" % (fromDate.year, string.zfill(fromDate.month, 2), string.zfill(fromDate.day, 2)))
                        out.writeTag("toDate", "%d%s%s" % (toDate.year, string.zfill(toDate.month, 2), string.zfill(toDate.day, 2)))
                        out.closeTag("line")
            else:
                out.openTag("line")
                out.writeTag("fromDate", "%d%s%s" % (adjusted_startDate.year, string.zfill(adjusted_startDate.month, 2), string.zfill(adjusted_startDate.day, 2)))
                out.writeTag("toDate", "%d%s%s" % (adjusted_endDate.year, string.zfill(adjusted_endDate.month, 2), string.zfill(adjusted_endDate.day, 2)))
                out.closeTag("line")

        mList = conf.getAllMaterialList()
        for mat in mList:
            if mat.canView(self.__aw) and mat.getTitle() != "Internal Page Files":
                if includeMaterial:
                    self._materialToXML(mat, vars, out=out)

        wm = webcast.HelperWebcastManager.getWebcastManagerInstance()
        url = wm.isOnAir(conf)
        wc = wm.getForthcomingWebcast(conf)
        if url:
            out.openTag("material")
            out.writeTag("ID","live webcast")
            out.writeTag("title","live webcast")
            out.writeTag("description","")
            out.writeTag("type","")
            out.writeTag("displayURL",url)
            out.closeTag("material")
        elif wc:
            out.openTag("material")
            out.writeTag("ID","forthcoming webcast")
            out.writeTag("title","forthcoming webcast")
            out.writeTag("description","")
            out.writeTag("type","")
            out.writeTag("displayURL", wm.getWebcastServiceURL(wc))
            out.closeTag("material")

        #plugins XML
        out.openTag("plugins")
        #we add all the information to be displayed by the plugins
        self._notify('meetingAndLectureDisplay', {'out': out, 'conf': conf, 'tz': tz})
        out.closeTag("plugins")


    def _sessionToXML(self,
                      session,
                      vars,
                      includeContribution,
                      includeMaterial,
                      includeSubContribution = 1,
                      showContribution       = None,
                      showSubContribution    = "all",
                      showWithdrawed         = True,
                      useSchedule            = True,
                      out                    = None,
                      recordingManagerTags   = None):

        if not out:
            out = self._XMLGen
        if vars and vars.has_key("frame") and vars["frame"] == "no":
            modificons = 0
        else:
            modificons = 1
        out.openTag("session", [["color", session.getColor()], ["textcolor", session.getTextColor()]])
        out.writeTag("ID", session.getId())

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
                self._userToXML(session, conv, out)
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
            tz = session.getConference().getTimezone()
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
                                    self._contribToXML(owner,vars,includeSubContribution,includeMaterial, session.getConference(),out=out, recordingManagerTags=recordingManagerTags) # needs to be re-done?
            else:
                for contrib in session.getContributionList():
                    if contrib.canView(self.__aw):
                        if showWithdrawed or not isinstance(contrib.getCurrentStatus(), conference.ContribStatusWithdrawn):
                            self._contribToXML(contrib, vars, includeSubContribution,includeMaterial, session.getConference(),out=out, recordingManagerTags=recordingManagerTags) # needs to be re-done

        mList = session.getAllMaterialList()
        for mat in mList:
            self._materialToXML(mat, vars, out=out)

        self._notify('addXMLMetadata', {'out': out, 'obj': session, 'type':"session", 'recordingManagerTags':recordingManagerTags})
        out.closeTag("session")

    def _slotToXML(self,slot,vars,includeContribution,includeMaterial, showWithdrawed=True, out=None, recordingManagerTags=None):
        if not out:
            out = self._XMLGen
        session = slot.getSession()
        conf = session.getConference()
        if vars and vars.has_key("frame") and vars["frame"] == "no":
            modificons = 0
        else:
            modificons = 1
        out.openTag("session", [["color", session.getColor()],["textcolor", session.getTextColor()]])
        out.writeTag("ID", session.getId())

        out.writeTag("parentProtection", dumps(session.getAccessController().isProtected()))
        out.writeTag("materialList", dumps(self._generateMaterialList(session)))


        slotId = session.getSortedSlotList().index(slot)
        slotCode = slotId + 1
        if session.getCode() not in ["no code", ""]:
            out.writeTag("code","%s-%s" % (session.getCode(),slotCode))
        else:
            out.writeTag("code","sess%s-%s" % (session.getId(),slotCode))
        if (session.canModify( self.__aw ) or session.canCoordinate(self.__aw)) and vars and modificons:
            out.writeTag("slotId", slotId)
            url = urlHandlers.UHSessionModifSchedule.getURL(session)
            ttLink = "%s#%s.s%sl%s" % (url, session.getStartDate().strftime('%Y%m%d'), session.getId(), slotId)
            out.writeTag("sessionTimetableLink",ttLink)
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
                self._userToXML(slot, conv, out)
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
                                self._contribToXML(owner,vars,1,includeMaterial, conf,out=out)
        mList = session.getAllMaterialList()
        for mat in mList:
            self._materialToXML(mat, vars, out=out)
        out.closeTag("session")

    def _contribToXML(self,
                      contribution,
                      vars,
                      includeSubContribution,
                      includeMaterial,
                      conf,
                      showSubContribution  = "all",
                      out                  = None,
                      recordingManagerTags = None):
        if not out:
            out = self._XMLGen
        if vars and vars.has_key("frame") and vars["frame"] == "no":
            modificons = 0
        else:
            modificons = 1
        out.openTag("contribution", [["color",contribution.getColor()],["textcolor",contribution.getTextColor()]])
        out.writeTag("ID",contribution.getId())

        out.writeTag("parentProtection", dumps(contribution.getAccessController().isProtected()))
        out.writeTag("materialList", dumps(self._generateMaterialList(contribution)))

        if contribution.getBoardNumber() != "":
            out.writeTag("board",contribution.getBoardNumber())
        if contribution.getTrack() != None:
            out.writeTag("track",contribution.getTrack().getTitle())
        if contribution.getType() != None:
            out.openTag("type")
            out.writeTag("id",contribution.getType().getId())
            out.writeTag("name",contribution.getType().getName())
            out.closeTag("type")
        if contribution.canModify( self.__aw ) and vars and modificons:
            out.writeTag("modifyLink",vars["contribModifyURLGen"](contribution))
        if (contribution.canModify( self.__aw ) or contribution.canUserSubmit(self.__aw.getUser())) and vars and modificons:
            out.writeTag("minutesLink", True)
        if (contribution.canModify( self.__aw ) or contribution.canUserSubmit(self.__aw.getUser())) and vars and modificons:
            out.writeTag("materialLink", True)
        keywords = contribution.getKeywords()
        keywords = keywords.replace("\r\n", "\n")
        keywordsList = filter (lambda a: a != '', keywords.split("\n"))
        if keywordsList:
            out.openTag("keywords")
            for keyword in keywordsList:
                out.writeTag("keyword",keyword.strip())
            out.closeTag("keywords")
        rnh = contribution.getReportNumberHolder()
        rns = rnh.listReportNumbers()
        if len(rns) != 0:
            for rn in rns:
                out.openTag("repno")
                out.writeTag("system",rn[0])
                out.writeTag("rn",rn[1])
                out.closeTag("repno")
        out.writeTag("title",contribution.title)
        sList = contribution.getSpeakerList()
        if len(sList) != 0:
            out.openTag("speakers")
            for sp in sList:
                self._userToXML(contribution, sp, out)
            if contribution.getSpeakerText() != "":
                out.writeTag("UnformatedUser",contribution.getSpeakerText())
            out.closeTag("speakers")
        primaryAuthorList = contribution.getPrimaryAuthorList()
        if len(primaryAuthorList) != 0:
            out.openTag("primaryAuthors")
            for sp in primaryAuthorList:
                self._userToXML(contribution, sp, out)
            out.closeTag("primaryAuthors")
        coAuthorList = contribution.getCoAuthorList()
        if len(coAuthorList) != 0:
            out.openTag("coAuthors")
            for sp in coAuthorList:
                self._userToXML(contribution, sp, out)
            out.closeTag("coAuthors")
        l = contribution.getLocation()
        if l != None or contribution.getRoom():
            out.openTag("location")
            if l!=None:
                out.writeTag("name",l.getName())
                out.writeTag("address",l.getAddress())
            if contribution.getRoom():
                roomName = self._getRoom(contribution.getRoom(), l)
                out.writeTag("room", roomName)
                url=RoomLinker().getURL(contribution.getRoom(), l)
                if url != "":
                    out.writeTag("roomMapURL",url)
            else:
                out.writeTag("room","")
            out.closeTag("location")
        tzUtil = DisplayTZ(self.__aw,conf)
        tz = tzUtil.getDisplayTZ()

        startDate = None
        if contribution.startDate:
            startDate = contribution.startDate.astimezone(timezone(tz))

        if startDate:
            endDate = startDate + contribution.duration
            out.writeTag("startDate","%d-%s-%sT%s:%s:00" %(startDate.year, string.zfill(startDate.month,2), string.zfill(startDate.day,2),string.zfill(startDate.hour,2), string.zfill(startDate.minute,2)))
            out.writeTag("endDate","%d-%s-%sT%s:%s:00" %(endDate.year, string.zfill(endDate.month,2), string.zfill(endDate.day,2),string.zfill(endDate.hour,2), string.zfill(endDate.minute,2)))
        if contribution.duration:
            out.writeTag("duration","%s:%s" %(string.zfill((datetime(1900,1,1)+contribution.duration).hour,2), string.zfill((datetime(1900,1,1)+contribution.duration).minute,2)))
        out.writeTag("abstract",contribution.getDescription())
        matList = contribution.getAllMaterialList()
        for mat in matList:
            if mat.canView(self.__aw):
                if includeMaterial:
                    self._materialToXML(mat, vars, out=out)
                else:
                    out.writeTag("material",out.writeTag("id",mat.id))
        for subC in contribution.getSubContributionList():
            if includeSubContribution:
                if showSubContribution == 'all' or str(showSubContribution) == str(subC.getId()):
                    self._subContributionToXML(subC, vars, includeMaterial, out=out, recordingManagerTags=recordingManagerTags)

        self._notify('addXMLMetadata', {'out': out, 'obj': contribution, 'type':"contribution", 'recordingManagerTags':recordingManagerTags})
        out.closeTag("contribution")


    def _subContributionToXML(self,
                              subCont,
                              vars,
                              includeMaterial,
                              out         = None,
                              recordingManagerTags = None):

        if not out:
            out = self._XMLGen
        if vars and vars.has_key("frame") and vars["frame"] == "no":
            modificons = 0
        else:
            modificons = 1
        out.openTag("subcontribution")
        out.writeTag("ID",subCont.getId())

        out.writeTag("parentProtection", dumps(subCont.getContribution().getAccessController().isProtected()))
        out.writeTag("materialList", dumps(self._generateMaterialList(subCont)))

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
            self._userToXML(subCont, sp, out)
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

        self._notify('addXMLMetadata', {'out': out, 'obj': subCont, 'type':"subcontribution", 'recordingManagerTags':recordingManagerTags})
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

        types = {"pdf"   :{"mapsTo" : "pdf",   "imgURL" : "%s/%s"%(Config.getInstance().getImagesBaseURL(), "pdf_small.png"),  "imgAlt" : "pdf file"},
                 "doc"   :{"mapsTo" : "doc",   "imgURL" : "%s/%s"%(Config.getInstance().getImagesBaseURL(), "word.png"),       "imgAlt" : "word file"},
                 "docx"  :{"mapsTo" : "doc",   "imgURL" : "%s/%s"%(Config.getInstance().getImagesBaseURL(), "word.png"),       "imgAlt" : "word file"},
                 "ppt"   :{"mapsTo" : "ppt",   "imgURL" : "%s/%s"%(Config.getInstance().getImagesBaseURL(), "powerpoint.png"), "imgAlt" : "powerpoint file"},
                 "pptx"  :{"mapsTo" : "ppt",   "imgURL" : "%s/%s"%(Config.getInstance().getImagesBaseURL(), "powerpoint.png"), "imgAlt" : "powerpoint file"},
                 "xls"   :{"mapsTo" : "xls",   "imgURL" : "%s/%s"%(Config.getInstance().getImagesBaseURL(), "excel.png"),      "imgAlt" : "excel file"},
                 "xlsx"  :{"mapsTo" : "xls",   "imgURL" : "%s/%s"%(Config.getInstance().getImagesBaseURL(), "excel.png"),      "imgAlt" : "excel file"},
                 "sxi"   :{"mapsTo" : "odp",   "imgURL" : "%s/%s"%(Config.getInstance().getImagesBaseURL(), "impress.png"),    "imgAlt" : "presentation file"},
                 "odp"   :{"mapsTo" : "odp",   "imgURL" : "%s/%s"%(Config.getInstance().getImagesBaseURL(), "impress.png"),    "imgAlt" : "presentation file"},
                 "sxw"   :{"mapsTo" : "odt",   "imgURL" : "%s/%s"%(Config.getInstance().getImagesBaseURL(), "writer.png"),     "imgAlt" : "writer file"},
                 "odt"   :{"mapsTo" : "odt",   "imgURL" : "%s/%s"%(Config.getInstance().getImagesBaseURL(), "writer.png"),     "imgAlt" : "writer file"},
                 "sxc"   :{"mapsTo" : "ods",   "imgURL" : "%s/%s"%(Config.getInstance().getImagesBaseURL(), "calc.png"),       "imgAlt" : "spreadsheet file"},
                 "ods"   :{"mapsTo" : "ods",   "imgURL" : "%s/%s"%(Config.getInstance().getImagesBaseURL(), "calc.png"),       "imgAlt" : "spreadsheet file"},
                 "other" :{"mapsTo" : "other", "imgURL" : "%s/%s"%(Config.getInstance().getImagesBaseURL(), "file_small.png"), "imgAlt" : "unknown type file"},
                 "link"  :{"mapsTo" : "link",  "imgURL" : "%s/%s"%(Config.getInstance().getImagesBaseURL(), "link.png"),       "imgAlt" : "link"}}

        if len(mat.getResourceList()) > 0:
            out.openTag("files")
            processedFiles = []
            for res in mat.getResourceList():
                try:
                    type = res.getFileType().lower()

                    try:
                        fileType = types[type]["mapsTo"]
                    except KeyError:
                        fileType = "other"

                    if vars:
                        filename = res.getFileName()
                        if filename in processedFiles:
                            filename = "%s-%s"%(processedFiles.count(filename)+1, filename)
                        out.openTag("file")
                        out.writeTag("name",filename)
                        out.writeTag("type", fileType)
                        out.writeTag("url",vars["resourceURLGen"](res))
                        out.closeTag("file")
                        processedFiles.append(res.getFileName())
                except:
                    out.openTag("file")
                    out.writeTag("name", str(res.getURL()))
                    out.writeTag("type", "link")
                    out.writeTag("url", str(res.getURL()))
                    out.closeTag("file")
            out.closeTag("files")

            # Used to enumerate types in the stylesheet. The order of the icons
            # showed for the materials will be the one specified here
            # TODO: find a way to avoid this hard coded list and get it from types
            # typeList = set([ type["mapsTo"] for type in types.values()])

            typeList = ["doc", "ppt", "pdf", "odt", "odp", "ods", "other", "link"]

            out.openTag("types")
            for type in typeList:
                out.openTag("type")
                out.writeTag("name", types[type]["mapsTo"])
                out.writeTag("imgURL", types[type]["imgURL"])
                out.writeTag("imgAlt", types[type]["imgAlt"])
                out.closeTag("type")
            out.closeTag("types")

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
        out.openTag("break", [["color", br.getColor()], ["textcolor", br.getTextColor()]])
        out.writeTag("name", br.getTitle())
        tzUtil = DisplayTZ(self.__aw, br.getOwner())
        tz = tzUtil.getDisplayTZ()
        startDate = br.getStartDate().astimezone(timezone(tz))
        endDate = br.getEndDate().astimezone(timezone(tz))
        out.writeTag("startDate", "%d-%s-%sT%s:%s:00" % (startDate.year, string.zfill(startDate.month, 2), string.zfill(startDate.day, 2), string.zfill(startDate.hour, 2), string.zfill(startDate.minute, 2)))
        out.writeTag("endDate", "%d-%s-%sT%s:%s:00" % (endDate.year, string.zfill(endDate.month, 2), string.zfill(endDate.day, 2), string.zfill(endDate.hour, 2), string.zfill(endDate.minute, 2)))
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


    def confToXML(self,
                  conf,
                  includeSession,
                  includeContribution,
                  includeMaterial,
                  showSession            = "all",
                  showContribution       = "all",
                  showSubContribution    = "all",
                  out                    = None,
                  overrideCache             = False,
                  recordingManagerTags   = None):
        """overrideCache = True apparently means force it NOT to use the cache. """

        if not out:
            out = self._XMLGen
        #try to get a cache
        version = "ses-%s_cont-%s_mat-%s_sch-%s" % (includeSession,
                                                    includeContribution,
                                                    includeMaterial,
                                                    False)
        obj = None
        if not overrideCache:
            obj = self.cache.loadObject(version, conf)
        if obj:
            xml = obj.getContent()
        else:
            temp = XMLGen(init=False)
            self._confToXML(conf,
                            None,
                            includeSession,
                            includeContribution,
                            includeMaterial,
                            showSession          = showSession,
                            showDate             = "all",
                            showContribution     = showContribution,
                            showSubContribution  = showSubContribution,
                            showWithdrawed       = False,
                            useSchedule          = False,
                            out                  = temp,
                            recordingManagerTags = recordingManagerTags)
            xml = temp.getXml()
            self.cache.cacheObject(version, xml, conf)

        out.writeXML(xml)


    def confToXMLMarc21(self,conf,includeSession=1,includeContribution=1,includeMaterial=1,out=None, overrideCache=False):

        if not out:
            out = self._XMLGen
        #try to get a cache
        version = "MARC21_ses-%s_cont-%s_mat-%s"%(includeSession,includeContribution,includeMaterial)
        obj = None
        if not overrideCache:
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

        out.openTag("datafield",[["tag","245"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield",conf.getTitle(),[["code","a"]])
        out.closeTag("datafield")

        out.writeTag("leader", "00000nmm  2200000uu 4500")
        out.openTag("datafield",[["tag","111"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield",conf.title,[["code","a"]])

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
                out.writeTag("subfield",loc,[["code","c"]])

        sd = conf.getStartDate()
        ed = conf.getEndDate()
        out.writeTag("subfield","%d-%s-%sT%s:%s:00Z" %(sd.year, string.zfill(sd.month,2), string.zfill(sd.day,2), string.zfill(sd.hour,2), string.zfill(sd.minute,2)),[["code","9"]])
        out.writeTag("subfield","%d-%s-%sT%s:%s:00Z" %(ed.year, string.zfill(ed.month,2), string.zfill(ed.day,2), string.zfill(ed.hour,2), string.zfill(ed.minute,2)),[["code","z"]])

        out.writeTag("subfield", uniqueId(conf),[["code","g"]])
        out.closeTag("datafield")

        for path in conf.getCategoriesPath():
            out.openTag("datafield",[["tag","650"],["ind1"," "],["ind2","7"]])
            out.writeTag("subfield", ":".join(path), [["code","a"]])
            out.closeTag("datafield")

        ####################################
        # Fermi timezone awareness         #
        ####################################
        #if conf.getStartDate() is not None:
        #    out.openTag("datafield",[["tag","518"],["ind1"," "],["ind2"," "]])
        #    out.writeTag("subfield","%d-%s-%sT%s:%s:00Z" %(conf.getStartDate().year, string.zfill(conf.getStartDate().month,2), string.zfill(conf.getStartDate().day,2), string.zfill(conf.getStartDate().hour,2), string.zfill(conf.getStartDate().minute,2)),[["code","d"]])
        #    out.closeTag("datafield")
        #sd = conf.getAdjustedStartDate(tz)
        sd = conf.getStartDate()
        if sd is not None:
            out.openTag("datafield",[["tag","518"],["ind1"," "],["ind2"," "]])
            out.writeTag("subfield","%d-%s-%sT%s:%s:00Z" %(sd.year, string.zfill(sd.month,2), string.zfill(sd.day,2), string.zfill(sd.hour,2), string.zfill(sd.minute,2)),[["code","d"]])
            out.closeTag("datafield")
        ####################################
        # Fermi timezone awareness(end)    #
        ####################################

        out.openTag("datafield",[["tag","520"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield",conf.getDescription(),[["code","a"]])
        out.closeTag("datafield")

        if conf.getReportNumberHolder().listReportNumbers():
            out.openTag("datafield",[["tag","088"],["ind1"," "],["ind2"," "]])
            for report in conf.getReportNumberHolder().listReportNumbers():
                out.writeTag("subfield",report[1],[["code","a"]])
            out.closeTag("datafield")


        out.openTag("datafield",[["tag","653"],["ind1","1"],["ind2"," "]])
        keywords = conf.getKeywords()
        keywords = keywords.replace("\r\n", "\n")
        for keyword in keywords.split("\n"):
            out.writeTag("subfield",keyword,[["code","a"]])
        out.closeTag("datafield")

        import MaKaC.webinterface.simple_event as simple_event
        import MaKaC.webinterface.meeting as meeting
        type = "Conference"
        if self.webFactory.getFactory(conf) == simple_event.WebFactory:
            type = "Lecture"
        elif self.webFactory.getFactory(conf) == meeting.WebFactory:
            type = "Meeting"
        out.openTag("datafield",[["tag","650"],["ind1","2"],["ind2","7"]])
        out.writeTag("subfield",type,[["code","a"]])
        out.closeTag("datafield")
        #### t o d o

        #out.openTag("datafield",[["tag","650"],["ind1","3"],["ind2","7"]])
        #out.writeTag("subfield",,[["code","a"]])
        #out.closeTag("datafield")


        # tag 700 chair name
        uList = conf.getChairList()
        for chair in uList:
            out.openTag("datafield",[["tag","906"],["ind1"," "],["ind2"," "]])
            nom = chair.getFamilyName() + " " + chair.getFirstName()
            out.writeTag("subfield",nom,[["code","p"]])
            out.writeTag("subfield",chair.getAffiliation(),[["code","u"]])
            out.closeTag("datafield")


        #out.openTag("datafield",[["tag","856"],["ind1","4"],["ind2"," "]])
        matList = conf.getAllMaterialList()
        for mat in matList:
            if mat.canView(self.__aw):
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
            out.openTag("datafield",[["tag","859"],["ind1"," "],["ind2"," "]])
            out.writeTag("subfield",chair.getEmail(),[["code","f"]])
            out.closeTag("datafield")

        edate = conf.getCreationDate()
        creaDate = datetime( edate.year, edate.month, edate.day )

        out.openTag("datafield",[["tag","961"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield","%d-%s-%sT"%(creaDate.year, string.zfill(creaDate.month,2), string.zfill(creaDate.day,2)),[["code","x"]])
        out.closeTag("datafield")

        edate = conf.getModificationDate()
        modifDate = datetime( edate.year, edate.month, edate.day )

        out.openTag("datafield",[["tag","961"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield","%d-%s-%sT"%(modifDate.year, string.zfill(modifDate.month,2), string.zfill(modifDate.day,2)),[["code","c"]])
        out.closeTag("datafield")

        out.openTag("datafield",[["tag","980"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield", self._getRecordCollection(conf), [["code","a"]])
        out.closeTag("datafield")

        out.openTag("datafield",[["tag","970"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield","INDICO." + uniqueId(conf),[["code","a"]])
        out.closeTag("datafield")

        self._generateLinkField(urlHandlers.UHConferenceDisplay, conf,
                                "Event details", out)

        self._generateAccessList(conf, out, specifyId=False)

    def contribToXMLMarc21(self,cont,includeMaterial=1, out=None, overrideCache=False):
        if not out:
            out = self._XMLGen
        #try to get a cache
        version = "MARC21_mat-%s"%(includeMaterial)
        obj = None
        if not overrideCache:
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

        out.writeTag("leader", "00000nmm  2200000uu 4500")
        out.openTag("datafield", [["tag", "035"], ["ind1", " "], ["ind2", " "]])
        out.writeTag("subfield", "INDICO.%s" % uniqueId(cont), [["code", "a"]])
        out.closeTag("datafield")

        out.openTag("datafield", [["tag", "035"], ["ind1", " "], ["ind2", " "]])
        out.writeTag("subfield", uniqueId(cont), [["code", "a"]])
        out.writeTag("subfield", "Indico", [["code", "9"]])
        out.closeTag("datafield")

        out.openTag("datafield", [["tag", "245"], ["ind1", " "], ["ind2", " "]])
        out.writeTag("subfield", cont.getTitle(), [["code", "a"]])
        out.closeTag("datafield")

        out.openTag("datafield", [["tag", "300"], ["ind1", " "], ["ind2", " "]])
        out.writeTag("subfield", cont.getDuration(), [["code", "a"]])
        out.closeTag("datafield")

        out.openTag("datafield", [["tag", "111"], ["ind1", " "], ["ind2", " "]])
        out.writeTag("subfield", uniqueId(cont.getConference()), [["code", "g"]])
        out.closeTag("datafield")

        edate = cont.getModificationDate()
        modifDate = datetime(edate.year, edate.month, edate.day)

        out.openTag("datafield", [["tag", "961"], ["ind1", " "], ["ind2", " "]])
        out.writeTag("subfield", "%d-%s-%sT" % (modifDate.year, string.zfill(modifDate.month, 2),
                     string.zfill(modifDate.day, 2)), [["code", "c"]])
        out.closeTag("datafield")

        for path in cont.getConference().getCategoriesPath():
            out.openTag("datafield", [["tag", "650"], ["ind1", " "], ["ind2", "7"]])
            out.writeTag("subfield", ":".join(path), [["code", "a"]])
            out.closeTag("datafield")

        l = cont.getLocation()
        if (l and l.getName() != "") or cont.getStartDate() is not None:
            out.openTag("datafield", [["tag", "518"], ["ind1", " "], ["ind2", " "]])
            if l:
                if l.getName() != "":
                    out.writeTag("subfield", l.getName(), [["code", "r"]])
            if cont.getStartDate() is not None:
                out.writeTag("subfield", "%d-%s-%sT%s:%s:00Z" % (cont.getStartDate().year,
                             string.zfill(cont.getStartDate().month, 2), string.zfill(cont.getStartDate().day, 2),
                             string.zfill(cont.getStartDate().hour, 2), string.zfill(cont.getStartDate().minute, 2)),
                             [["code", "d"]])
                out.writeTag("subfield", "%d-%s-%sT%s:%s:00Z" % (cont.getEndDate().year,
                             string.zfill(cont.getEndDate().month, 2), string.zfill(cont.getEndDate().day, 2),
                             string.zfill(cont.getEndDate().hour, 2), string.zfill(cont.getEndDate().minute, 2)),
                             [["code", "h"]])
            out.closeTag("datafield")

        out.openTag("datafield", [["tag", "520"], ["ind1", " "], ["ind2", " "]])
        out.writeTag("subfield", cont.getDescription(), [["code", "a"]])
        out.closeTag("datafield")

        out.openTag("datafield", [["tag", "611"], ["ind1", "2"], ["ind2", "4"]])
        out.writeTag("subfield", cont.getConference().getTitle(), [["code", "a"]])
        out.closeTag("datafield")


        if cont.getReportNumberHolder().listReportNumbers():
            out.openTag("datafield",[["tag","088"],["ind1"," "],["ind2"," "]])
            for report in cont.getReportNumberHolder().listReportNumbers():
                out.writeTag("subfield",report[1],[["code","a"]])
            out.closeTag("datafield")

        out.openTag("datafield",[["tag","653"],["ind1","1"],["ind2"," "]])
        keywords = cont.getKeywords()
        keywords = keywords.replace("\r\n", "\n")
        for keyword in keywords.split("\n"):
            out.writeTag("subfield",keyword,[["code","a"]])
        out.closeTag("datafield")

        out.openTag("datafield",[["tag","650"],["ind1","1"],["ind2","7"]])
        out.writeTag("subfield","SzGeCERN",[["code","2"]])
        if cont.getTrack():
            out.writeTag("subfield",cont.getTrack().getTitle(),[["code","a"]])
        out.closeTag("datafield")

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
            out.openTag("datafield",[["tag","100"],["ind1"," "],["ind2"," "]])
            fullName = auth.getFamilyName() + " " + auth.getFirstName()
            out.writeTag("subfield",fullName,[["code","a"]])
            for val in list[user]:
                out.writeTag("subfield",val,[["code","e"]])
            out.writeTag("subfield",auth.getAffiliation(),[["code","u"]])
            out.closeTag("datafield")
            del list[auth]

        for user in list.keys():
            out.openTag("datafield",[["tag","700"],["ind1"," "],["ind2"," "]])
            fullName = user.getFamilyName() + " " + user.getFirstName()
            out.writeTag("subfield",fullName,[["code","a"]])
            for val in list[user]:
                out.writeTag("subfield",val,[["code","e"]])
            out.writeTag("subfield",user.getAffiliation(),[["code","u"]])
            out.closeTag("datafield")

        matList = cont.getAllMaterialList()
        for mat in matList:
            if mat.canView(self.__aw):
                if includeMaterial:
                    self.materialToXMLMarc21(mat, out=out)

        out.openTag("datafield",[["tag","962"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield","INDICO.%s"%uniqueId(cont.getConference()),[["code","b"]])
        out.closeTag("datafield")

        out.openTag("datafield",[["tag","970"],["ind1"," "],["ind2"," "]])
        confcont = "INDICO." + uniqueId(cont)
        out.writeTag("subfield",confcont,[["code","a"]])
        out.closeTag("datafield")

        out.openTag("datafield",[["tag","980"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield", self._getRecordCollection(cont), [["code","a"]])
        out.closeTag("datafield")

        self._generateLinkField(urlHandlers.UHContributionDisplay,
                                cont, "Contribution details", out)
        self._generateLinkField(urlHandlers.UHConferenceDisplay,
                                cont.getConference(), "Event details", out)

        self._generateAccessList(cont, out, specifyId=False)
    ####
    #fb


    def subContribToXMLMarc21(self,subCont,includeMaterial=1, out=None, overrideCache=False):
        if not out:
            out = self._XMLGen
        #try to get a cache
        version = "MARC21_mat-%s"%(includeMaterial)
        obj = None
        if not overrideCache:
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

        out.writeTag("leader", "00000nmm  2200000uu 4500")
        out.openTag("datafield",[["tag","035"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield","INDICO.%s" % (uniqueId(subCont)), [["code","a"]])
        out.closeTag("datafield")
    #
        out.openTag("datafield",[["tag","035"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield",uniqueId(subCont), [["code","a"]])
        out.writeTag("subfield","Indico",[["code","9"]])
        out.closeTag("datafield")

        out.openTag("datafield",[["tag","245"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield",subCont.getTitle(),[["code","a"]])
        out.closeTag("datafield")

        out.openTag("datafield",[["tag","300"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield",subCont.getDuration(),[["code","a"]])
        out.closeTag("datafield")

        out.openTag("datafield",[["tag","111"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield", uniqueId(subCont.getConference()), [["code","g"]])
        out.closeTag("datafield")

        if subCont.getReportNumberHolder().listReportNumbers():
            out.openTag("datafield",[["tag","088"],["ind1"," "],["ind2"," "]])
            for report in subCont.getReportNumberHolder().listReportNumbers():
                out.writeTag("subfield",report[1],[["code","a"]])
            out.closeTag("datafield")


        out.openTag("datafield",[["tag","653"],["ind1","1"],["ind2"," "]])
        keywords = subCont.getKeywords()
        keywords = keywords.replace("\r\n", "\n")
        for keyword in keywords.split("\n"):
            out.writeTag("subfield",keyword,[["code","a"]])
        out.closeTag("datafield")


        for path in subCont.getConference().getCategoriesPath():
            out.openTag("datafield",[["tag","650"],["ind1"," "],["ind2","7"]])
            out.writeTag("subfield", ":".join(path), [["code","a"]])
            out.closeTag("datafield")

        l=subCont.getLocation()
        if (l and l.getName() != "") or subCont.getContribution().getStartDate() is not None:
            out.openTag("datafield",[["tag","518"],["ind1"," "],["ind2"," "]])
            if l:
                if l.getName() != "":
                    out.writeTag("subfield",l.getName(),[["code","r"]])
            if subCont.getContribution().getStartDate() is not None:
                out.writeTag("subfield","%d-%s-%sT%s:%s:00Z" %(subCont.getContribution().getStartDate().year, string.zfill(subCont.getContribution().getStartDate().month,2), string.zfill(subCont.getContribution().getStartDate().day,2), string.zfill(subCont.getContribution().getStartDate().hour,2), string.zfill(subCont.getContribution().getStartDate().minute,2)),[["code","d"]])
            out.closeTag("datafield")
    #
        out.openTag("datafield",[["tag","520"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield",subCont.getDescription(),[["code","a"]])
        out.closeTag("datafield")

        out.openTag("datafield",[["tag","611"],["ind1","2"],["ind2","4"]])
        out.writeTag("subfield",subCont.getConference().getTitle(),[["code","a"]])
        out.closeTag("datafield")
    #
        out.openTag("datafield",[["tag","650"],["ind1","1"],["ind2","7"]])
        out.writeTag("subfield","SzGeCERN",[["code","2"]])
        if subCont.getContribution().getTrack():
            out.writeTag("subfield",subCont.getContribution().getTrack().getTitle(),[["code","a"]])
        out.closeTag("datafield")


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
            out.openTag("datafield",[["tag","100"],["ind1"," "],["ind2"," "]])
            fullName = auth.getFamilyName() + " " + auth.getFirstName()
            out.writeTag("subfield",fullName,[["code","a"]])
            for val in list[user]:
                out.writeTag("subfield",val,[["code","e"]])
            out.writeTag("subfield",auth.getAffiliation(),[["code","u"]])
            out.closeTag("datafield")
            del list[auth]

        for user in list.keys():
            out.openTag("datafield",[["tag","700"],["ind1"," "],["ind2"," "]])
            fullName = user.getFamilyName() + " " + user.getFirstName()
            out.writeTag("subfield",fullName,[["code","a"]])
            for val in list[user]:
                out.writeTag("subfield",val,[["code","e"]])
            out.writeTag("subfield",user.getAffiliation(),[["code","u"]])
            out.closeTag("datafield")

        matList = subCont.getAllMaterialList()
        for mat in matList:
            if mat.canView(self.__aw):
                if includeMaterial:
                    self.materialToXMLMarc21(mat, out=out)

        out.openTag("datafield",[["tag","962"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield","INDICO.%s"%uniqueId(subCont.getConference()),[["code","b"]])
        out.closeTag("datafield")

        out.openTag("datafield",[["tag","970"],["ind1"," "],["ind2"," "]])
        confcont = "INDICO." + uniqueId(subCont)
        out.writeTag("subfield",confcont,[["code","a"]])
        out.closeTag("datafield")

        out.openTag("datafield",[["tag","980"],["ind1"," "],["ind2"," "]])
        out.writeTag("subfield", self._getRecordCollection(subCont), [["code","a"]])
        out.closeTag("datafield")

        self._generateLinkField(urlHandlers.UHSubContributionDisplay, subCont,
                                "Contribution details", out)
        self._generateLinkField(urlHandlers.UHConferenceDisplay,
                                subCont.getConference(), "Event details", out)

        self._generateAccessList(subCont, out, specifyId=None)


    def materialToXMLMarc21(self,mat, out=None):
        if not out:
            out = self._XMLGen
        rList = mat.getResourceList()
        self.resourcesToXMLMarc21(rList, out=out)

    def resourcesToXMLMarc21(self, rList, out=None):
        if not out:
            out = self._XMLGen

        for res in rList:
            if res.canAccess(self.__aw):
                self.resourceToXMLMarc21(res, out=out)
                self._generateAccessList(res, out)

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

        out.openTag("datafield",[["tag","856"],["ind1","4"],["ind2"," "]])
        out.writeTag("subfield",res.getDescription(),[["code","a"]])
        out.writeTag("subfield",res.getURL(),[["code","u"]])
        out.writeTag("subfield", "INDICO.%s" % \
                     uniqueId(res), [["code", "3"]])
        out.writeTag("subfield", "resource", [["code","x"]])
        out.writeTag("subfield", "external", [["code","z"]])
        out.writeTag("subfield", res.getOwner().getTitle(), [["code","y"]])
        out.closeTag("datafield")

    def resourceFileToXMLMarc21(self,res, out=None):
        if not out:
            out = self._XMLGen

        out.openTag("datafield",[["tag","856"],["ind1","4"],["ind2"," "]])
        out.writeTag("subfield",res.getDescription(),[["code","a"]])
        try:
            out.writeTag("subfield",res.getSize(),[["code","s"]])
        except:
            pass

        url = str(urlHandlers.UHFileAccess.getURL( res ))
        out.writeTag("subfield",url,[["code","u"]])
        out.writeTag("subfield", "INDICO.%s" % \
                     uniqueId(res), [["code", "3"]])
        out.writeTag("subfield", res.getFileName(), [["code","y"]])
        out.writeTag("subfield", "stored", [["code","z"]])
        out.writeTag("subfield", "resource", [["code","x"]])
        out.closeTag("datafield")

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


    def isDirty(self, mtime, object):
        modDate = resolveHierarchicalId(object.getId())._modificationDS
        fileModDate = timezone("UTC").localize(
            datetime.utcfromtimestamp(mtime))

        # check file system date vs. event date
        return (modDate > fileModDate)

    def _generatePath(self, entry):
        """
        Generate the actual hierarchical location
        """

        # a205.0 -> /cachedir/a/a2/a205/0

        tree = entry.getId().split('.')
        return [tree[0][0], tree[0][0:2]] + tree
