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

from cStringIO import StringIO
import MaKaC.webinterface.pages.sessions as sessions
import MaKaC.webinterface.pages.conferences as conferences
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.locators as locators
import MaKaC.webinterface.materialFactories as materialFactories
import MaKaC.user as user
import MaKaC.conference as conference
import MaKaC.schedule as schedule
import MaKaC.domain as domain
import re
from MaKaC.webinterface.rh.base import RoomBookingDBMixin
from MaKaC.webinterface.rh.conferenceBase import RHSessionBase
from MaKaC.webinterface.rh.conferenceBase import RHSessionBase, RHSessionSlotBase, RHSubmitMaterialBase
from MaKaC.webinterface.rh.base import RHModificationBaseProtected
from MaKaC.errors import MaKaCError, FormValuesError, NoReportError
import MaKaC.webinterface.pages.errors as errors
import MaKaC.common.filters as filters
import MaKaC.webinterface.common.contribFilters as contribFilters
from MaKaC.webinterface.common.contribStatusWrapper import ContribStatusList
from MaKaC.webinterface.common.slotDataWrapper import Slot
from MaKaC.PDFinterface.conference import ContribsToPDF
from indico.core.config import Config
from BTrees.OOBTree import OOBTree
from BTrees.IOBTree import IOBTree
from datetime import datetime,timedelta,date
from MaKaC.errors import FormValuesError
from MaKaC.conference import SessionChair
from MaKaC.i18n import _
from pytz import timezone
from indico.web.flask.util import send_file

class RHSessionModifBase( RHSessionBase, RHModificationBaseProtected ):

    def _checkParams( self, params ):
        RHSessionBase._checkParams( self, params )

    def _checkProtection( self ):
        RHModificationBaseProtected._checkProtection( self )

    def _displayCustomPage( self, wf ):
        return None

    def _displayDefaultPage( self ):
        return None

    def _process( self ):
        wf = self.getWebFactory()
        if wf != None:
            res = self._displayCustomPage( wf )
            if res != None:
                return res
        return self._displayDefaultPage()


class RHSessionModCoordinationBase(RHSessionModifBase):

    def _checkProtection(self):
        if self._target.isClosed():
            raise NoReportError(_("""The modification of the session "%s" is not allowed because it is closed""")%self._target.getTitle())
        if self._target.canCoordinate(self.getAW()):
            return
        RHSessionModifBase._checkProtection( self )

class RHSessionModUnrestrictedContribMngCoordBase(RHSessionModifBase):

    def _checkProtection(self):
        if self._target.isClosed():
            raise NoReportError(_("""The modification of the session "%s" is not allowed because it is closed""")%self._target.getTitle())
        if self._target.canCoordinate(self.getAW(), "modifContribs"):
            return
        RHSessionModifBase._checkProtection( self )

class RHSessionModification(RHSessionModifBase):
    _uh = urlHandlers.UHSessionModification

    def _checkProtection(self):
        if self._target.canCoordinate(self.getAW()):
            return
        RHSessionModifBase._checkProtection( self )

    def _process( self ):
        if self._session.isClosed():
            p = sessions.WPSessionModificationClosed( self, self._session )
        else:
            wf = self.getWebFactory()
            p = sessions.WPSessionModification( self, self._session )
            if wf != None:
                p = wf.getSessionModification(self, self._session)
        return p.display()

#--------------------------------------------------------------------------


class RHSessionDataModification(RoomBookingDBMixin, RHSessionModifBase):
    _uh = urlHandlers.UHSessionDataModification

    def _checkParams(self, params):
        RHSessionModifBase._checkParams(self, params)
        self._confirmed = "confirm" in params
        self._action = ""
        if "CANCEL" in params or "cancel" in params:
            self._action = "CANCEL"
        elif "OK" in params or "confirm" in params:
            self._action = "MODIFY"
        elif "performedAction" in params:
            self._action = params["performedAction"]
        else:
            params["title"] = self._session.getTitle()
            params["code"] = self._session.getCode()
            params["description"] = self._session.getDescription()
            cdur = self._session.getContribDuration()
            params["durHour"], params["durMin"] = int(
                cdur.seconds / 3600), int((cdur.seconds % 3600) / 60)
            params["tt_type"] = self._session.getScheduleType()

        self._evt = self._session

    def _modify(self, params):
        self._target.setValues(params, 1)
        self._target.setScheduleType(
            params.get("tt_type", self._target.getScheduleType()))

    def _process(self):
        url = urlHandlers.UHSessionModification.getURL(self._target)
        params = self._getRequestParams()
        if self._action == "CANCEL":
            self._redirect(url)
            return
        elif self._action == "MODIFY":
            title = str(params.get("title", ""))
            if title.strip() == "":
                raise NoReportError("session title cannot be empty")
            else:
                newSchType = params.get(
                    "tt_type", self._target.getScheduleType())
                if self._target.getScheduleType() != newSchType and\
                        not self._confirmed:
                    p = sessions.WPModEditDataConfirmation(self, self._target)
                    del params["confId"]
                    del params["sessionId"]
                    del params["OK"]
                    return p.display(**params)
                self._modify(params)
                self._redirect(url)
                return
        p = sessions.WPSessionDataModification(self, self._target)
        wf = self.getWebFactory()
        if wf is not None:
            p = wf.getSessionDataModification(self, self._target)
        params = self._getRequestParams()
        return p.display(**params)

    def _removePersons(self, params, typeName):
        persons = self._normaliseListParam(params.get("%ss" % typeName, []))
        """
        List of persons is indexed by their ID in the apropriate
        list in session
        """
        list = None
        if typeName == "convener":
            list = self._session.getConvenerList()

        for p in persons:
            perspntoRemove = None
            if typeName == "convener":
                personToRemove = self._session.getConvenerById(p)
            list.remove(personToRemove)


#-------------------------------------------------------------------------------------

class RHSessionClose( RHSessionModifBase ):
    _uh = urlHandlers.UHSessionClose

    def _checkParams(self, params):
        RHSessionModifBase._checkParams(self, params)
        self._confirm = params.has_key("confirm")
        self._cancel = params.has_key("cancel")

    def _process( self ):
        if self._cancel:
            self._redirect(urlHandlers.UHSessionModifTools.getURL(self._target))
        elif self._confirm:
            self._target.setClosed(True)
            self._redirect(urlHandlers.UHSessionModification.getURL(self._target))
        else:
            return sessions.WPSessionClosing(self, self._target).display()

class RHSessionOpen( RHSessionModifBase ):
    _uh = urlHandlers.UHSessionOpen

    def _process( self ):
        self._target.setClosed(False)
        self._redirect(urlHandlers.UHSessionModification.getURL(self._target))


class RHMaterials(RHSessionModCoordinationBase):
    def _checkParams(self, params):
        RHSessionModCoordinationBase._checkParams(self, params)

        params["days"] = params.get("day", "all")
        if params.get("day", None) is not None :
            del params["day"]

    def _process(self):
        if self._target.getOwner().isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p.display()

        p = sessions.WPSessionModifMaterials( self, self._target )
        return p.display(**self._getRequestParams())



class RHMaterialsAdd(RHSubmitMaterialBase, RHSessionModCoordinationBase):
    _uh = urlHandlers.UHSessionModifMaterials

    def __init__(self, req):
        RHSessionModCoordinationBase.__init__(self, req)
        RHSubmitMaterialBase.__init__(self)

    def _checkParams(self, params):
        RHSessionModCoordinationBase._checkParams(self, params)
        RHSubmitMaterialBase._checkParams(self, params)


class RHSessionModifSchedule(RoomBookingDBMixin, RHSessionModCoordinationBase):
    _uh = urlHandlers.UHSessionModifSchedule

    def _checkParams(self,params):
        RHSessionModCoordinationBase._checkParams(self,params)
        params["days"] = params.get("day", "all")
        if params.get("day", None) is not None:
            del params["day"]

    def _process( self ):
        if self._session.isClosed():
            p = sessions.WPSessionModificationClosed( self, self._session )
        else:
            p = sessions.WPSessionModifSchedule(self,self._session)
            wf = self.getWebFactory()
            if wf != None:
               p = wf.getSessionModifSchedule(self,self._session)

        params = self._getRequestParams()
        return p.display(**params)


class RHSessionModifAC( RHSessionModifBase ):
    _uh = urlHandlers.UHSessionModifAC

    def _process( self ):
        if self._session.isClosed():
            p = sessions.WPSessionModificationClosed( self, self._session )
        else:
            p = sessions.WPSessionModifAC( self, self._session )
            wf = self.getWebFactory()
            if wf != None:
                p = wf.getSessionModifAC(self, self._session)
        return p.display()


class RHSessionSetVisibility( RHSessionModifBase ):
    _uh = urlHandlers.UHSessionSetVisibility

    def _checkParams( self, params ):
        RHSessionModifBase._checkParams( self, params )
        if params.has_key("changeToPrivate"):
            self._protect = 1
        elif params.has_key("changeToInheriting"):
            self._protect = 0
        elif params.has_key("changeToPublic"):
            self._protect = -1

    def _process( self ):
        self._session.setProtection( self._protect )
        self._redirect( urlHandlers.UHSessionModifAC.getURL( self._session ) )

class RHSessionModifComm( RHSessionModCoordinationBase ):
    _uh = urlHandlers.UHSessionModifComm

    def _process( self ):
        if self._session.isClosed():
            p = sessions.WPSessionModificationClosed( self, self._session )
        else:
            p = sessions.WPSessionModifComm( self, self._session )
            wf = self.getWebFactory()
            if wf != None:
                p = wf.getSessionModifComm(self, self._session)
        return p.display()

class RHSessionModifCommEdit( RHSessionModifComm ):
    _uh = urlHandlers.UHSessionModifCommEdit

    def _checkParams(self,params):
        RHSessionModifBase._checkParams( self, params )
        self._action=""
        if params.has_key("OK"):
            self._action="UPDATE"
            self._comment=params.get("content","")

        elif params.has_key("CANCEL"):
            self._action="CANCEL"

    def _process(self):
        if self._action=="UPDATE":
            self._session.setComments(self._comment)
            self._redirect(urlHandlers.UHSessionModifComm.getURL(self._session))
            return
        elif self._action=="CANCEL":
            self._redirect(urlHandlers.UHSessionModifComm.getURL(self._session))
            return
        p=sessions.WPSessionCommEdit(self,self._session)
        wf = self.getWebFactory()
        if wf != None:
            p = wf.getSessionModifCommEdit(self, self._session)
        return p.display()


class RHSessionModifTools( RHSessionModifBase ):
    _uh = urlHandlers.UHSessionModifTools

    def _process( self ):
        if self._session.isClosed():
            p = sessions.WPSessionModificationClosed( self, self._session )
        else:
            p = sessions.WPSessionModifTools( self, self._session )
            wf = self.getWebFactory()
            if wf != None:
                p = wf.getSessionModifTools(self, self._session)
        return p.display()


class RHSessionDeletion( RHSessionModifBase ):
    _uh = urlHandlers.UHSessionDeletion

    def _checkParams( self, params ):
        RHSessionModifBase._checkParams( self, params )
        self._confirm = params.has_key( "confirm" )
        self._cancel = params.has_key( "cancel" )

    def _process( self ):
        if self._cancel:
            self._redirect( urlHandlers.UHSessionModifTools.getURL( self._session ) )
        elif self._confirm:
            self._conf.removeSession( self._session )
            self._redirect( urlHandlers.UHConfModifSchedule.getURL( self._conf ) )
        else:
            return sessions.WPSessionDeletion( self, self._session ).display()

class RHFitSlot(RHSessionModCoordinationBase):

    def _checkParams(self, params):
        RHSessionModCoordinationBase._checkParams(self, params)
        self._slotID = params.get("slotId","")
        self._slot=self._target.getSlotById(self._slotID)
        self._sessionID = params.get("sessionId","")
        self._targetDay=params.get("day","")

    def _process(self):
        if self._slot is not None:
            self._slot.fit()
        self._redirect("%s#%s.s%sl%s"%(urlHandlers.UHConfModifSchedule.getURL(self._conf), self._targetDay, self._sessionID, self._slotID))

class RHSlotCalc(RHSessionModCoordinationBase):

    def _checkParams(self, params):
        RHSessionModifBase._checkParams(self, params)
        self._slotId=params.get("slotId","")
        self._cancel=params.has_key("CANCEL")
        self._ok=params.has_key("OK")
        self._hour=params.get("hour","")
        self._minute=params.get("minute","")
        self._action=params.get("action","duration")
        self._currentDay = params.get("currentDay", "")
        self._inSessionTimetable = (params.get("inSessionTimetable", "no") == "yes")

        if self._ok:
            if self._hour.strip() == "" or self._minute.strip() == "":
                raise MaKaCError( _("Please write the time with the format HH:MM. For instance, 00:05 to indicate 'O hours' and '5 minutes'"))
            try:
                if int(self._hour) or int(self._hour):
                    pass
            except ValueError, e:
                raise MaKaCError( _("Please write a number to specify the time HH:MM. For instance, 00:05 to indicate 'O hours' and '5 minutes'"))

    def _formatRedirectURL(self, baseURL):
        target = "".join([str(baseURL),
                        "#",
                       self._currentDay,
                        ".s",
                        self._session.getId(),
                        "l",
                        self._slotId])

        return target

    def _process(self):
        if not self._cancel:
            slot=self._target.getSlotById(self._slotId)
            if not self._ok:
                p=sessions.WPModSlotCalc(self,slot)
                return p.display()
            else:
                t=timedelta(hours=int(self._hour), minutes=int(self._minute))
                slot.recalculateTimes(self._action, t)

        if (self._inSessionTimetable):
            self._redirect(self._formatRedirectURL(urlHandlers.UHSessionModifSchedule.getURL(self._session)))
        else:
            self._redirect(self._formatRedirectURL(urlHandlers.UHConfModifSchedule.getURL(self._conf)))


class ContribFilterCrit(filters.FilterCriteria):
    _availableFields = { \
        contribFilters.TypeFilterField.getId():contribFilters.TypeFilterField, \
        contribFilters.StatusFilterField.getId():contribFilters.StatusFilterField, \
        contribFilters.AuthorFilterField.getId():contribFilters.AuthorFilterField, \
        contribFilters.MaterialFilterField.getId():contribFilters.MaterialFilterField, \
        contribFilters.TrackFilterField.getId():contribFilters.TrackFilterField }

class ContribSortingCrit(filters.SortingCriteria):
    _availableFields={\
        contribFilters.NumberSF.getId():contribFilters.NumberSF,
        contribFilters.DateSF.getId():contribFilters.DateSF,
        contribFilters.ContribTypeSF.getId():contribFilters.ContribTypeSF,
        contribFilters.TrackSF.getId():contribFilters.TrackSF,
        contribFilters.SpeakerSF.getId():contribFilters.SpeakerSF,
        contribFilters.BoardNumberSF.getId():contribFilters.BoardNumberSF,
        contribFilters.SessionSF.getId():contribFilters.SessionSF,
        contribFilters.TitleSF.getId():contribFilters.TitleSF
    }


class RHContribList(RHSessionModCoordinationBase):
    _uh = urlHandlers.UHSessionModContribList

    def _checkParams( self, params ):
        RHSessionModCoordinationBase._checkParams( self, params )
        filterUsed=params.has_key("OK")
        #sorting
        self._sortingCrit=ContribSortingCrit([params.get("sortBy","number").strip()])
        self._order = params.get("order","down")
        #filtering
        filter = {"author":params.get("authSearch","")}
        ltypes = []
        if not filterUsed:
            for type in self._conf.getContribTypeList():
                ltypes.append(type.getId())
        else:
            for id in self._normaliseListParam(params.get("types",[])):
                ltypes.append(id)
        filter["type"]=ltypes
        ltracks = []
        if not filterUsed:
            for track in self._conf.getTrackList():
                ltracks.append( track.getId() )
        filter["track"]=self._normaliseListParam(params.get("tracks",ltracks))
        lstatus=[]
        if not filterUsed:
            for status in ContribStatusList().getList():
                lstatus.append(ContribStatusList().getId(status))
        filter["status"]=self._normaliseListParam(params.get("status",lstatus))
        lmaterial=[]
        if not filterUsed:
            paperId=materialFactories.PaperFactory().getId()
            slidesId=materialFactories.SlidesFactory().getId()
            for matId in ["--other--","--none--",paperId,slidesId]:
                lmaterial.append(matId)
        filter["material"]=self._normaliseListParam(params.get("material",lmaterial))
        self._filterCrit=ContribFilterCrit(self._conf,filter)
        typeShowNoValue,trackShowNoValue=True,True
        if filterUsed:
            typeShowNoValue =  params.has_key("typeShowNoValue")
            trackShowNoValue =  params.has_key("trackShowNoValue")
        self._filterCrit.getField("type").setShowNoValue( typeShowNoValue )
        self._filterCrit.getField("track").setShowNoValue( trackShowNoValue )

    def _process( self ):
        p=sessions.WPModContribList(self,self._target)
        return p.display(filterCrit=self._filterCrit,
                        sortingCrit=self._sortingCrit, order=self._order)


class RHContribListEditContrib(RHSessionModCoordinationBase):
    _uh = urlHandlers.UHSessionModContribListEditContrib

    def _checkParams(self,params):
        l = locators.WebLocator()
        l.setContribution( params )
        self._contrib=l.getObject()
        self._conf=self._contrib.getConference()
        self._target=self._session=self._contrib.getSession()
        RHSessionModCoordinationBase._checkParams(self,params)
        self._action=""
        if params.has_key("OK"):
            self._action="GO"
        elif params.has_key("CANCEL"):
            self._action="CANCEL"
        self._sortBy=params.get("sortBy","")

    def _process( self ):
        url=urlHandlers.UHSessionModContribList.getURL(self._session)
        if self._sortBy!="":
            url.addParam("sortBy",self._sortBy)
        if self._action=="GO":
            params = self._getRequestParams()
            #if params["locationAction"] == "inherit":
            #    params["locationName"] = ""
            #if params["roomAction"] == "inherit":
            #    params["roomName"] = ""
            self._contrib.setValues(params)
            self._redirect(url)
        elif self._action=="CANCEL":
            self._redirect(url)
        else:
            p=sessions.WPModContribListEditContrib(self,self._contrib)
            return p.display(sortBy=self._sortBy)


class RHSchEditContrib(RHSessionModCoordinationBase):

    def _checkParams(self,params):
        #RHSessionModifBase._checkParams(self,params)
        self._check = int(params.get("check",1))
        self._moveEntries = int(params.get("moveEntries",0))
        l = locators.WebLocator()
        l.setContribution( params )
        self._contrib=l.getObject()
        self._conf=self._contrib.getConference()
        self._target=self._session=self._contrib.getSession()
        self._action=""
        if params.has_key("OK"):
            self._action="GO"
        elif params.has_key("CANCEL"):
            self._action="CANCEL"

    def _process(self):
        url=urlHandlers.UHSessionModifSchedule.getURL(self._session)
        if self._action=="GO":
            params = self._getRequestParams()
            self._contrib.setValues(params,self._check, self._moveEntries)
            self._redirect(url)
        elif self._action=="CANCEL":
            self._redirect(url)
        else:
            p=sessions.WPModSchEditContrib(self,self._contrib)
            return p.display()


class RHAddContribs(RHSessionModUnrestrictedContribMngCoordBase):
    _uh = urlHandlers.UHSessionModAddContribs

    def _checkParams(self,params):
        RHSessionModifBase._checkParams(self,params)
        self._action=""
        conf=self._target.getConference()
        self._contribIdList=self._normaliseListParam(params.get("manSelContribs",[]))+params.get("selContribs","").split(",")+self._normaliseListParam(params.get("contributions",[]))
        if params.has_key("OK"):
            self._action="ADD"
            track=conf.getTrackById(params.get("selTrack",""))
            if track is not None:
                for contrib in track.getContributionList():
                    self._contribIdList.append(contrib.getId())
        elif params.has_key("CANCEL"):
            self._action="CANCEL"
        elif params.has_key("CONFIRM"):
            self._action="ADD_CONFIRMED"
        elif params.has_key("CONFIRM_ALL"):
            self._action="ADD_ALL_CONFIRMED"

    def _needsWarning(self,contrib):
        return (contrib.getSession() is not None and \
                            contrib.getSession()!=self._target) or \
                            (contrib.getSession() is None and \
                            contrib.isScheduled())

    def _process( self ):
        url=urlHandlers.UHSessionModContribList.getURL(self._target)
        if self._action=="CANCEL":
            self._redirect(url)
            return
        elif self._action in ("ADD","ADD_CONFIRMED","ADD_ALL_CONFIRMED"):
            contribList=[]
            for id in self._contribIdList:
                contrib=self._conf.getContributionById(id)
                if contrib is None:
                    continue
                if self._needsWarning(contrib):
                    if self._action=="ADD":
                        p=sessions.WPModImportContribsConfirmation(self,self._target)
                        return p.display(contribIds=self._contribIdList)
                    elif self._action=="ADD_CONFIRMED":
                        continue
                contribList.append(contrib)
            for contrib in contribList:
                contrib.setSession(self._target)
            self._redirect(url)
            return
        else:
            p=sessions.WPModAddContribs(self,self._target)
            return p.display()

class RHContribQuickAccess(RHSessionModifBase):

    def _checkParams(self,params):
        RHSessionModifBase._checkParams(self,params)
        self._contrib=self._target.getConference().getContributionById(params.get("selContrib",""))

    def _process(self):
        url=urlHandlers.UHSessionModContribList.getURL(self._target)
        if self._contrib is not None:
            url=urlHandlers.UHContributionModification.getURL(self._contrib)
        self._redirect(url)

class RHContribsActions:
    """
    class to select the action to do with the selected contributions
    """
    def __init__(self, req):
        assert req is None

    def process(self, params):
        if 'REMOVE' in params:
            return RHRemContribs(None).process(params)
        elif 'PDF' in params:
            return RHContribsToPDF(None).process(params)
        elif 'AUTH' in params:
            return RHContribsParticipantList(None).process(params)
        return "no action to do"

class RHRemContribs(RHSessionModUnrestrictedContribMngCoordBase):
    _uh = urlHandlers.UHSessionModContributionAction

    def _checkParams(self,params):
        RHSessionModifBase._checkParams(self,params)
        self._contribs=[]
        for id in self._normaliseListParam(params.get("contributions",[])):
            contrib=self._target.getConference().getContributionById(id)
            if contrib is not None:
                self._contribs.append(contrib)

    def _process(self):
        url=urlHandlers.UHSessionModContribList.getURL(self._target)
        for contrib in self._contribs:
            self._target.removeContribution(contrib)
        self._redirect(url)

class RHContribsToPDF(RHSessionModUnrestrictedContribMngCoordBase):

    def _checkParams( self, params ):
        RHSessionModifBase._checkParams( self, params )
        self._contribIds = self._normaliseListParam( params.get("contributions", []) )
        self._contribs = []
        for id in self._contribIds:
            self._contribs.append(self._conf.getContributionById(id))

    def _process(self):
        tz = self._conf.getTimezone()
        if not self._contribs:
            return "No contributions to print"
        pdf = ContribsToPDF(self._conf, self._contribs)
        return send_file('Contributions.pdf', pdf.generate(), 'PDF')


class RHContribQuickAccess(RHSessionModCoordinationBase):

    def _checkParams(self,params):
        RHSessionModCoordinationBase._checkParams(self,params)
        self._contrib=self._target.getConference().getContributionById(params.get("selContrib",""))

    def _process(self):
        url=urlHandlers.UHSessionModContribList.getURL(self._target)
        if self._contrib is not None:
            url=urlHandlers.UHContributionModification.getURL(self._contrib)
        self._redirect(url)


class RHContribsParticipantList(RHSessionModUnrestrictedContribMngCoordBase):

    def _checkProtection( self ):
        if len( self._conf.getCoordinatedTracks( self._getUser() ) ) == 0:
            RHSessionModUnrestrictedContribMngCoordBase._checkProtection( self )

    def _checkParams( self, params ):
        RHSessionModifBase._checkParams( self, params )
        self._contribIds = self._normaliseListParam( params.get("contributions", []) )
        self._displayedGroups = self._normaliseListParam( params.get("displayedGroups", []) )
        self._clickedGroup = params.get("clickedGroup","")

    def _setGroupsToDisplay(self):
        if self._clickedGroup in self._displayedGroups:
            self._displayedGroups.remove(self._clickedGroup)
        else:
            self._displayedGroups.append(self._clickedGroup)

    def _process( self ):
        if not self._contribIds:
            self._redirect(urlHandlers.UHSessionModContribList.getURL(self._target))
            return #"<table align=\"center\" width=\"100%%\"><tr><td>There are no contributions</td></tr></table>"

        speakers = OOBTree()
        primaryAuthors = OOBTree()
        coAuthors = OOBTree()
        speakerEmails = set()
        primaryAuthorEmails = set()
        coAuthorEmails = set()

        self._setGroupsToDisplay()
        for contribId in self._contribIds:
            contrib = self._conf.getContributionById(contribId)
            #Primary authors
            for pAut in contrib.getPrimaryAuthorList():
                if pAut.getFamilyName().lower().strip() == "" and pAut.getFirstName().lower().strip() == "" and pAut.getEmail().lower().strip() == "":
                    continue
                keyPA = "%s-%s-%s"%(pAut.getFamilyName().lower(), pAut.getFirstName().lower(), pAut.getEmail().lower())
                if contrib.isSpeaker(pAut):
                    speakers[keyPA] = pAut
                    speakerEmails.add(pAut.getEmail())
                primaryAuthors[keyPA] = pAut
                primaryAuthorEmails.add(pAut.getEmail())
            #Co-authors
            for coAut in contrib.getCoAuthorList():
                if coAut.getFamilyName().lower().strip() == "" and coAut.getFirstName().lower().strip() == "" and coAut.getEmail().lower().strip() == "":
                    continue
                keyCA = "%s-%s-%s"%(coAut.getFamilyName().lower(), coAut.getFirstName().lower(), coAut.getEmail().lower())
                if contrib.isSpeaker(coAut):
                    speakers[keyCA] = coAut
                    speakerEmails.add(coAut.getEmail())
                coAuthors[keyCA] = coAut
                coAuthorEmails.add(coAut.getEmail())
        emailList = {"speakers":{},"primaryAuthors":{},"coAuthors":{}}
        emailList["speakers"]["tree"] = speakers
        emailList["primaryAuthors"]["tree"] = primaryAuthors
        emailList["coAuthors"]["tree"] = coAuthors
        emailList["speakers"]["emails"] = speakerEmails
        emailList["primaryAuthors"]["emails"] = primaryAuthorEmails
        emailList["coAuthors"]["emails"] = coAuthorEmails
        p = sessions.WPModParticipantList(self, self._target, emailList, self._displayedGroups, self._contribIds )
        return p.display()


class RHRelocate(RHSessionModUnrestrictedContribMngCoordBase):

    def _checkParams(self, params):
        RHSessionModUnrestrictedContribMngCoordBase._checkParams(self, params)
        self._entry=None
        if params.has_key("contribId"):
            self._entry=self._conf.getContributionById(params.get("contribId",""))
        else:
            raise MaKaCError( _("No contribution to relocate"))
        self._contribPlace=params.get("targetId","")
        self._cancel=params.has_key("CANCEL")
        self._ok=params.has_key("OK")
        self._targetDay=params.get("targetDay","")
        self._check=int(params.get("check","1"))

    def _process(self):
        if not self._cancel:
            if not self._ok:
                p=sessions.WPSessionModifRelocate(self,self._session, self._entry, self._targetDay)
                return p.display()
            else:
                if self._contribPlace!="conf":
                    s,ss=self._contribPlace.split(":")
                    session=self._conf.getSessionById(s)
                    if session is not None:
                        slot=session.getSlotById(ss)
                        if slot is not None:
                            self._entry.getSchEntry().getSchedule().removeEntry(self._entry.getSchEntry())
                            self._entry.setSession(session)
                            slot.getSchedule().addEntry(self._entry.getSchEntry(), check=self._check)
                else:
                    self._entry.getSchEntry().getSchedule().removeEntry(self._entry.getSchEntry())
                    self._entry.setSession(None)
                    self._conf.getSchedule().addEntry(self._entry.getSchEntry(), check=self._check)
        self._redirect("%s#%s"%(urlHandlers.UHSessionModifSchedule.getURL(self._session), self._targetDay))




