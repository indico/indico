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

import os
import shutil
from cStringIO import StringIO
import tempfile
import types
from flask import session, request
from persistent.list import PersistentList
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta
from pytz import timezone
import MaKaC.common.timezoneUtils as timezoneUtils
from MaKaC.common.contextManager import ContextManager
from BTrees.OOBTree import OOBTree
from MaKaC.webinterface.common.abstractDataWrapper import AbstractParam
import MaKaC.review as review
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.materialFactories as materialFactories
import MaKaC.webinterface.displayMgr as displayMgr
import MaKaC.webinterface.internalPagesMgr as internalPagesMgr
import MaKaC.webinterface.pages.conferences as conferences
import MaKaC.webinterface.pages.sessions as sessions
import MaKaC.conference as conference
from MaKaC.webinterface.general import *
from MaKaC.webinterface.rh.base import RHModificationBaseProtected, RoomBookingDBMixin
from MaKaC.webinterface.rh.base import RH   # Strange conflict was here: this line vs nothing
from MaKaC.webinterface.pages import admins
from MaKaC.webinterface.rh.conferenceBase import RHConferenceBase, RHAlarmBase, RHSubmitMaterialBase
from MaKaC.webinterface.rh.categoryDisplay import UtilsConference
from indico.core.config import Config
from MaKaC.errors import MaKaCError, FormValuesError,ModificationError,\
    ConferenceClosedError, NoReportError, NotFoundError
from MaKaC.PDFinterface.conference import ConfManagerAbstractsToPDF, ContribsToPDF, RegistrantsListToBadgesPDF, LectureToPosterPDF
from MaKaC.webinterface.common import AbstractStatusList, abstractFilters
from MaKaC.webinterface import locators
from MaKaC.common.xmlGen import XMLGen
from MaKaC.webinterface.common.abstractNotificator import EmailNotificator
import MaKaC.webinterface.common.registrantNotificator as registrantNotificator
import MaKaC.common.filters as filters
import MaKaC.webinterface.common.contribFilters as contribFilters
from MaKaC.webinterface.common.contribStatusWrapper import ContribStatusList
from MaKaC.common.contribPacker import ZIPFileHandler,AbstractPacker, ContribPacker,ConferencePacker, ProceedingsPacker
from MaKaC.conference import CustomRoom
from MaKaC.common import pendingQueues
from MaKaC.export.excel import AbstractListToExcel, ParticipantsListToExcel, ContributionsListToExcel
from MaKaC.common import utils
from MaKaC.i18n import _
from indico.util.i18n import i18nformat
from MaKaC.plugins.base import Observable
from MaKaC.common.timezoneUtils import nowutc
from MaKaC.review import AbstractStatusSubmitted, AbstractStatusProposedToAccept, AbstractStatusProposedToReject
import MaKaC.webinterface.pages.abstracts as abstracts
from MaKaC.rb_tools import FormMode
from MaKaC.webinterface.common.tools import cleanHTMLHeaderFilename
from MaKaC.fossils.conference import ISessionBasicFossil
from indico.modules.scheduler import Client
from indico.util import json
from indico.web.http_api.metadata.serializer import Serializer
from indico.web.flask.util import send_file
from MaKaC.PDFinterface.base import LatexRunner


class RHConferenceModifBase( RHConferenceBase, RHModificationBaseProtected ):

    def _checkParams( self, params ):
        RHConferenceBase._checkParams( self, params )

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


class RHConferenceModification( RoomBookingDBMixin, RHConferenceModifBase ):
    _uh = urlHandlers.UHConferenceModification

    def _process( self ):
        pars={}
        wf=self.getWebFactory()
        if wf is not None:
            pars["type"]=wf.getId()
        if self._conf.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p.display(**pars)
        else:
            p = conferences.WPConferenceModification( self, self._target )

            if wf is not None:
                p = wf.getConfModif(self, self._conf)
            return p.display(**pars)


class RHConfScreenDatesEdit(RHConferenceModifBase):
    _uh = urlHandlers.UHConfScreenDatesEdit

    def _checkParams(self,params):
        RHConferenceModifBase._checkParams(self,params)
        self._action=""
        if params.has_key("CANCEL"):
            self._action="CANCEL"
        elif params.has_key("OK"):
            self._action="EDIT"
            self._sDate,self._eDate=None,None
            tz = self._target.getTimezone()
            if params.get("start_date","conference")=="own":
                try:
                    self._sDate=timezone(tz).localize(datetime(int(params["sYear"]),
                                    int(params["sMonth"]),
                                    int(params["sDay"]),
                                    int(params["sHour"]),
                                    int(params["sMin"]))).astimezone(timezone('UTC'))
                except ValueError:
                    raise MaKaCError( _("Please enter integers in all the start date fields"), _("Schedule"))
            if params.get("end_date","conference")=="own":
                try:
                    self._eDate=timezone(tz).localize(datetime(int(params["eYear"]),
                                    int(params["eMonth"]),
                                    int(params["eDay"]),
                                    int(params["eHour"]),
                                    int(params["eMin"]))).astimezone(timezone('UTC'))
                except ValueError:
                    raise MaKaCError( _("Please enter integers in all the end date fields"), _("Schedule"))

    def _process( self ):
        url=urlHandlers.UHConferenceModification.getURL(self._target)
        if self._action=="CANCEL":
            self._redirect(url)
            return
        elif self._action=="EDIT":
            self._target.setScreenStartDate(self._sDate)
            self._target.setScreenEndDate(self._eDate)
            self._redirect(url)
            return
        p = conferences.WPScreenDatesEdit(self, self._target)
        return p.display()


class RHConferenceModifKey(RHConferenceModifBase):

    def _checkParams(self, params):
        RHConferenceBase._checkParams(self, params)
        self._modifkey = params.get("modifKey", "").strip()
        self._doNotSanitizeFields.append("modifKey")
        self._redirectURL = params.get("redirectURL", "")

    def _checkProtection(self):
        modif_keys = session.setdefault('modifKeys', {})
        modif_keys[self._conf.getId()] = self._modifkey
        session.modified = True

        RHConferenceModifBase._checkProtection(self)

    def _process( self ):
        if self._redirectURL != "":
            url = self._redirectURL
        else:
            url = urlHandlers.UHConferenceDisplay.getURL( self._conf )
        self._redirect( url )

class RHConferenceModifManagementAccess( RHConferenceModifKey ):
    _uh = urlHandlers.UHConfManagementAccess
    _tohttps = True

    def _checkParams(self, params):
        RHConferenceModifKey._checkParams(self, params)
        from MaKaC.webinterface.rh.reviewingModif import RCPaperReviewManager, RCReferee
        self._isRegistrar = self._target.isRegistrar( self._getUser() )
        self._isPRM = RCPaperReviewManager.hasRights(self)
        self._isReferee = RCReferee.hasRights(self)
        self._isPluginManagerOrAdmin = any(self._notify("isPluginTypeAdmin", {"user": self._getUser()}) +
                                           self._notify("isPluginAdmin", {"user": self._getUser(), "plugins": "any"}) +
                                           self._notify("isPluginManager", {"user": self._getUser(), "conf": self._target, "plugins": "any"}))

    def _checkProtection(self):
        if not (self._isRegistrar or self._isPRM or self._isReferee or self._isPluginManagerOrAdmin):
            RHConferenceModifKey._checkProtection(self)

    def _process( self ):
        url = None
        if self._redirectURL != "":
            url = self._redirectURL

        elif self._conf.canModify(self.getAW()):
            url = urlHandlers.UHConferenceModification.getURL( self._conf )

        elif self._isRegistrar:
            url = urlHandlers.UHConfModifRegForm.getURL( self._conf )
        elif self._isPRM:
            url = urlHandlers.UHConfModifReviewingPaperSetup.getURL( self._conf )
        elif self._isReferee:
            url = urlHandlers.UHConfModifReviewingAssignContributionsList.getURL( self._conf )
        elif self._isPluginManagerOrAdmin:
            urls = self._notify("conferencePluginManagementURL", {"conf": self._target, "secure": self.use_https()})
            if urls:
                url = urls[0]
        if not url:
            url = urlHandlers.UHConfManagementAccess.getURL( self._conf )

        self._redirect( url )


class RHConferenceCloseModifKey(RHConferenceBase):

    def _checkParams(self, params):
        RHConferenceBase._checkParams(self, params)
        self._modifkey = params.get("modifKey", "").strip()
        self._doNotSanitizeFields.append("modifKey")
        self._redirectURL = params.get("redirectURL", "")

    def _process(self):
        modif_keys = session.get("modifKeys")
        if modif_keys and modif_keys.pop(self._conf.getId(), None):
            session.modified = True
        if self._redirectURL != "":
            url = self._redirectURL
        else:
            url = urlHandlers.UHConferenceDisplay.getURL(self._conf)
        self._redirect(url)


class RHConferenceClose(RHConferenceModifBase):
    _uh = urlHandlers.UHConferenceClose

    def _checkParams(self, params):
        RHConferenceBase._checkParams(self, params)
        self._confirm = params.has_key("confirm")
        self._cancel = params.has_key("cancel")

    def _process(self):

        if self._cancel:
            url = urlHandlers.UHConferenceModification.getURL(self._conf)
            self._redirect(url)
        elif self._confirm:
            self._target.setClosed(True)
            url = urlHandlers.UHConferenceModification.getURL(self._conf)
            self._redirect(url)
        else:
            return conferences.WPConfClosing(self, self._conf).display()


class RHConferenceOpen(RHConferenceModifBase):
    _allowClosed = True

    def _checkProtection(self):
        RHConferenceModifBase._checkProtection(self)

        user = self._getUser()
        if user is self._conf.getCreator():
            return
        # If we are not the creator, check if we have category admin privileges
        hasAccess = False
        for owner in self._conf.getOwnerList():
            if owner.canUserModify(user): # category or system admin
                hasAccess = True
                break
        if not hasAccess:
            if self._conf.isClosed():
                raise ConferenceClosedError(self._target.getConference())
            else:
                raise ModificationError()

    def _checkParams(self, params):
        RHConferenceBase._checkParams(self, params)

    def _process(self):
        self._target.setClosed(False)
        url = urlHandlers.UHConferenceModification.getURL(self._conf)
        self._redirect(url)


class RHConfDataModif(RoomBookingDBMixin, RHConferenceModifBase):
    _uh = urlHandlers.UHConfDataModif

    def _displayCustomPage(self, wf):
        return None

    def _displayDefaultPage(self):
        p = conferences.WPConfDataModif(self, self._target)
        pars = {}
        wf = self.getWebFactory()
        if wf is not None:
            pars["type"] = wf.getId()
        return p.display(**pars)


class RHConfPerformDataModif( RoomBookingDBMixin, RHConferenceModifBase ):
    _uh = urlHandlers.UHConfPerformDataModif

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        if params.get("title", "").strip() =="" and not ("cancel" in params):
            raise FormValuesError("Please, provide a name for the event")
        self._cancel = params.has_key("cancel")

    def _process( self ):
        if not self._cancel:
            UtilsConference.setValues( self._conf, self._getRequestParams() )
        self._redirect( urlHandlers.UHConferenceModification.getURL( self._conf) )


#----------------------------------------------------------------

class RHConfModifSchedule( RoomBookingDBMixin, RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModifSchedule

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        params["sessions"] = self._normaliseListParam( params.get("session", []) )
        params["slot"] = params.get("slot", [])
        params["days"] = params.get("day", "all")
        params["contributions"] = self._normaliseListParam( params.get("contribution", []) )
        if params.get("session", None) is not None :
            del params["session"]
        if params.get("day", None) is not None :
            del params["day"]

    def _process( self ):

        # The timetable management page shouldn't be cached
        self._disableCaching();

        params = self._getRequestParams()

        if self._conf.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p.display()
        elif params['sessions'] == []:
            p = conferences.WPConfModifScheduleGraphic( self, self._target )

            wf=self.getWebFactory()
            if wf is not None:
                p=wf.getConfModifSchedule( self, self._target )
            return p.display(**params)
        else:

            session = self._target.getSessionById(params['sessions'][0])

            p = sessions.WPSessionModifSchedule( self, session )

            wf=self.getWebFactory()
            if wf is not None:
                p=wf.getSessionModifSchedule( self, session )
            return p.display(**params)

class RHScheduleDataEdit(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModScheduleDataEdit

    def _checkParams(self,params):
        RHConferenceModifBase._checkParams(self,params)
        self._action=""
        if params.has_key("CANCEL"):
            self._action="CANCEL"
        elif params.has_key("OK"):
            self._action="EDIT"
            self._sDate,self._eDate=None,None
            try:
                self._sDate=datetime(int(params["sYear"]),
                                    int(params["sMonth"]),
                                    int(params["sDay"]),
                                    int(params["sHour"]),
                                    int(params["sMin"]))
            except ValueError:
                raise MaKaCError( _("Please enter integers in all the start date fields"), _("Schedule"))
            try:
                self._eDate=datetime(int(params["eYear"]),
                                    int(params["eMonth"]),
                                    int(params["eDay"]),
                                    int(params["eHour"]),
                                    int(params["eMin"]))
            except ValueError:
                raise MaKaCError( _("Please enter integers in all the end date fields"), _("Schedule"))

    def _process( self ):
        url=urlHandlers.UHConfModifSchedule.getURL(self._target)
        if self._action=="CANCEL":
            self._redirect(url)
            return
        elif self._action=="EDIT":
            #
            # The times are naive relative to the conference tz, must
            # convert to UTC.
            #
            confTZ = self._target.getTimezone()
            sd = timezone(confTZ).localize(datetime(self._sDate.year,
                                                    self._sDate.month,
                                                    self._sDate.day,
                                                    self._sDate.hour,
                                                    self._sDate.minute))
            sdUTC = sd.astimezone(timezone('UTC'))
            ed = timezone(confTZ).localize(datetime(self._eDate.year,
                                                    self._eDate.month,
                                                    self._eDate.day,
                                                    self._eDate.hour,
                                                    self._eDate.minute))
            edUTC = ed.astimezone(timezone('UTC'))
            self._target.setDates(sdUTC,edUTC)
            self._redirect(url)
            return
        p=conferences.WPModScheduleDataEdit(self,self._target)
        return p.display()


class RConferenceGetSessions(RHConferenceModifBase):

    def _process(self):
        from MaKaC.common.fossilize import fossilize
        return json.dumps(fossilize(self._conf.getSessionList(), ISessionBasicFossil))


#-------------------------------------------------------------------------------------


class RHConfModifAC( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModifAC

    def _process( self ):
        if self._conf.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p.display()
        else:
            p = conferences.WPConfModifAC( self, self._target)
            wf=self.getWebFactory()
            if wf is not None:
                p = wf.getConfModifAC(self, self._conf)
            return p.display()


class RHConfSetVisibility( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfSetVisibility

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        if params.has_key("changeToPrivate"):
            self._protectConference = 1
        elif params.has_key("changeToInheriting"):
            self._protectConference = 0
        elif params.has_key("changeToPublic"):
            self._protectConference = -1

    def _process( self ):
        self._conf.setProtection( self._protectConference )
        self._redirect( urlHandlers.UHConfModifAC.getURL( self._conf ) )

class RHConfGrantSubmissionToAllSpeakers( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfGrantSubmissionToAllSpeakers

    def _process( self ):
        for cont in self._target.getContributionList():
            speakers = cont.getSpeakerList()[:]
            for sCont in cont.getSubContributionList():
                speakers += sCont.getSpeakerList()[:]
            for speaker in speakers:
                cont.grantSubmission(speaker,False)
        self._redirect( urlHandlers.UHConfModifAC.getURL( self._target ) )

class RHConfRemoveAllSubmissionRights( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfRemoveAllSubmissionRights

    def _process( self ):
        for cont in self._target.getContributionList():
            cont.revokeAllSubmitters()
        self._redirect( urlHandlers.UHConfModifAC.getURL( self._target ) )

class RHConfGrantModificationToAllConveners( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfGrantModificationToAllConveners

    def _process( self ):
        for ses in self._target.getSessionList():
            for slot in ses.getSlotList():
                for convener in slot.getConvenerList():
                    ses.grantModification(convener,False)
        self._redirect( urlHandlers.UHConfModifAC.getURL( self._target ) )

class RHConfModifTools( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModifTools
    _allowClosed = True

    def _process( self ):
        p = conferences.WPConfDisplayAlarm(self, self._target)
        return p.display()

class RHConfDeletion( RoomBookingDBMixin, RHConferenceModifBase ):
    _uh = urlHandlers.UHConfDeletion

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._confirm = params.has_key( "confirm" )
        self._cancel = params.has_key( "cancel" )

    def _process( self ):
        if self._cancel:
            self._redirect( urlHandlers.UHConfModifTools.getURL( self._conf ) )
        elif self._confirm:
            parent=None
            if self._conf.getOwnerList()!=[]:
                parent=self._conf.getOwnerList()[0]
            self._conf.delete()
            if parent is not None:
                self._redirect( urlHandlers.UHCategoryModification.getURL(parent) )
            else:
                self._redirect( urlHandlers.UHWelcome.getURL() )
        else:
            return conferences.WPConfDeletion( self, self._conf ).display()

class RHConfModifParticipants( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModifParticipants

    def _process( self ):
        if self._conf.isClosed():
            return conferences.WPConferenceModificationClosed( self, self._target ).display()
        else:
            return conferences.WPConfModifParticipants( self, self._target ).display()

class RHConfModifParticipantsSetup(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifParticipantsSetup

    def _process( self ):
        if self._conf.isClosed():
            return conferences.WPConferenceModificationClosed( self, self._target ).display()
        else:
            return conferences.WPConfModifParticipantsSetup( self, self._target ).display()

class RHConfModifParticipantsPending(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifParticipantsPending

    def _process( self ):
        if self._conf.isClosed():
            return conferences.WPConferenceModificationClosed( self, self._target ).display()
        elif self._target.getParticipation().getPendingParticipantList() and nowutc() < self._target.getStartDate():
            return conferences.WPConfModifParticipantsPending( self, self._target ).display()
        else:
            return self._redirect(RHConfModifParticipants._uh.getURL(self._conf))

class RHConfModifParticipantsDeclined(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifParticipantsDeclined

    def _process( self ):
        if self._conf.isClosed():
            return conferences.WPConferenceModificationClosed( self, self._target ).display()
        elif self._target.getParticipation().getDeclinedParticipantList():
            return conferences.WPConfModifParticipantsDeclined( self, self._target ).display()
        else:
            return self._redirect(RHConfModifParticipants._uh.getURL(self._conf))


class RHConfModifParticipantsAction(RHConfModifParticipants):
    _uh = urlHandlers.UHConfModifParticipantsAction

    def _process( self ):
        params = self._getRequestParams()
        selectedList = self._normaliseListParam(self._getRequestParams().get("participants",[]))
        toList = []
        if selectedList == []:
            raise FormValuesError(_("No participant selected! Please select at least one."))
        else:
            for id in selectedList :
                participant = self._conf.getParticipation().getParticipantById(id)
                toList.append(participant)
        excel = ParticipantsListToExcel(self._conf, list=toList)
        return send_file('ParticipantList.csv', StringIO(excel.getExcelFile()), 'CSV')


class RHConfModifParticipantsStatistics(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifParticipantsStatistics

    def _process( self ):
        if self._conf.isClosed():
            return conferences.WPConferenceModificationClosed( self, self._target ).display()
        else:
            return conferences.WPConfModifParticipantsStatistics( self, self._target ).display()

#######################################################################################

class RHConfAllParticipants( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfAllSessionsConveners

    def _process(self):
        p = conferences.WPConfAllParticipants( self, self._conf )
        return p.display()


class RHConfModifLog (RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifLog

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams( self, params )

        if params.get("view",None) is not None :
            if params["view"] == "Action Log" :
                params["view"] = "action"
            elif params["view"] == "Email Log" :
                params["view"] = "email"
            elif params["view"] == "Custom Log" :
                params["view"] = "custom"
            elif params["view"] == "General Log" :
                params["view"] = "general"

    def  _process(self):
        params = self._getRequestParams()
        p = conferences.WPConfModifLog( self, self._target )
        return p.display(**params)

#######################################################################################

class RHConfClone( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfClone
    _allowClosed = True

    def _process( self ):
        p = conferences.WPConfClone( self, self._conf )
        wf=self.getWebFactory()
        if wf is not None:
            p = wf.getConfClone(self, self._conf)
        return p.display()


#######################################################################################

class RHConfAllSessionsConveners( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfAllSessionsConveners

    def _process(self):
        p = conferences.WPConfAllSessionsConveners( self, self._conf )
#        wf=self.getWebFactory()
#        if wf is not None:
#            p = wf.getConfClone(self, self._conf)

        return p.display()

class RHConfAllSessionsConvenersAction( RHConferenceModifBase ):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams(self, params)
        self._selectedConveners = self._normaliseListParam(params.get("conveners",[]))

    def _process( self ):
        if len(self._selectedConveners)>0:
            p = conferences.WPEMailConveners(self, self._conf, self._selectedConveners)
            return p.display()
        else:
            self._redirect(urlHandlers.UHConfAllSessionsConveners.getURL(self._conf))

class RHConvenerSendEmail( RHConferenceModifBase  ):

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams( self, params )

        self._toEmails = []
        cclist = []

        self._send = params.has_key("OK")
        if self._send:
            if len(params.get("toEmails","").strip()) > 0 :
                self._toEmails = (params.get("toEmails","").strip()).split(",")
            else :
                raise FormValuesError( _("'To' address list is empty"))
            if params.get("from","") == "":
                raise FormValuesError( _("Please write from address"))
            if params.get("subject","") == "":
                raise FormValuesError( _("Please write a subject for the email"))
            if params.get("body","") == "":
                raise FormValuesError( _("Please write a body for the email"))
            #####cclist emails
            cclist = params.get("cc","").strip().split(",")
            # remove empty elements
            if '' in cclist:
                cclist.remove('')
            # strip all the elements in the list
            cclist = map(lambda x: x.strip(), cclist)
            #####

        self._params={}
        self._params["subject"]=params["subject"]
        self._params["from"]=params["from"]
        self._params["body"]=params["body"]
        self._params["cc"]=cclist
        self._params["conf"] = self._conf
        self._preview = params.has_key("preview")

    def _process(self):
        if self._send:
            self._params['to'] = self._toEmails
            registrantNotificator.EmailNotificator().notifyAll(self._params)
            p = conferences.WPConvenerSentEmail(self, self._target)
            return p.display()
        else:
            self._redirect(urlHandlers.UHConfAllSessionsConveners.getURL(self._conf))

#######################################################################################


class RHConfAllSpeakers( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfAllSpeakers

    def _process(self):
        p = conferences.WPConfAllSpeakers( self, self._conf )
        return p.display()

class RHConfAllSpeakersAction( RHConferenceModifBase ):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams(self, params)
        self._selectedSpeakers = self._normaliseListParam(params.get("participants",[]))

    def _process( self ):

        if len(self._selectedSpeakers)>0:
            p = conferences.WPEMailContribParticipants(self, self._conf, self._selectedSpeakers)
            return p.display()
        else:
            self._redirect(urlHandlers.UHConfAllSpeakers.getURL(self._conf))

class RHContribParticipantsSendEmail( RHConferenceModifBase  ):

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams( self, params )

        self._toEmails = []
        cclist = []

        self._send = params.has_key("OK")
        if self._send:
            if len(params.get("toEmails","").strip()) > 0 :
                self._toEmails = (params.get("toEmails","").strip()).split(",")
            else :
                raise FormValuesError( _("'To' address list is empty"))
            if params.get("from","") == "":
                raise FormValuesError( _("Please write from address"))
            if params.get("subject","") == "":
                raise FormValuesError( _("Please write a subject for the email"))
            if params.get("body","") == "":
                raise FormValuesError( _("Please write a body for the email"))
            #####cclist emails
            cclist = params.get("cc","").strip().split(",")
            # remove empty elements
            if '' in cclist:
                cclist.remove('')
            # strip all the elements in the list
            cclist = map(lambda x: x.strip(), cclist)
            #####

        self._params={}
        self._params["subject"]=params["subject"]
        self._params["from"]=params["from"]
        self._params["body"]=params["body"]
        self._params["cc"]=cclist
        self._params["conf"] = self._conf
        self._preview = params.has_key("preview")

    def _process(self):
        if self._send:
            self._params['to'] = self._toEmails
            registrantNotificator.EmailNotificator().notifyAll(self._params)
            p = conferences.WPContribParticipationSentEmail(self, self._target)
            return p.display()
        else:
            self._redirect(urlHandlers.UHConfAllSpeakers.getURL(self._conf))


#######################################################################################


class RHConfPerformCloning( RoomBookingDBMixin, RHConferenceModifBase, Observable ):
    """
    New version of clone functionality -
    fully replace the old one, based on three different actions,
    adds mechanism of selective cloning of materials and access
    privileges attached to an event
    """
    _uh = urlHandlers.UHConfPerformCloning
    _cloneType = "none"
    _allowClosed = True

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._date = datetime.today()
        self._cloneType = params.get("cloneType", None)
        if self._cloneType is None:
            raise FormValuesError( _("""Please choose a cloning interval for this event"""))
        elif self._cloneType == "once" :
            self._date = datetime( int(params["stdyo"]), \
                                int(params["stdmo"]), \
                                int(params["stddo"]), \
                                int(self._conf.getAdjustedStartDate().hour), \
                                int(self._conf.getAdjustedStartDate().minute) )
        elif self._cloneType == "intervals" :
            self._date = datetime( int(params["indyi"]), \
                                int(params["indmi"]), \
                                int(params["inddi"]), \
                                int(self._conf.getAdjustedStartDate().hour), \
                                int(self._conf.getAdjustedStartDate().minute) )
        elif self._cloneType == "days" :
            self._date = datetime( int(params["indyd"]), \
                                int(params["indmd"]), \
                                int(params["inddd"]), \
                                int(self._conf.getAdjustedStartDate().hour), \
                                int(self._conf.getAdjustedStartDate().minute) )
        self._confirm = params.has_key( "confirm" )
        self._cancel = params.has_key( "cancel" )

    def _process( self ):
        params = self._getRequestParams()
        paramNames = params.keys()
        options = { "materials"     : "cloneMaterials"    in paramNames,
                    "access"        : "cloneAccess"       in paramNames,
                    "keys"          : "cloneAccess"       in paramNames,
                    "authors"       : "cloneTimetable"    in paramNames,
                    "contributions" : "cloneTimetable"    in paramNames,
                    "subcontribs"   : "cloneTimetable"    in paramNames,
                    "sessions"      : "cloneTimetable"    in paramNames,
                    "tracks"        : "cloneTracks"       in paramNames,
                    "registration"  : "cloneRegistration" in paramNames,
                    "abstracts"     : "cloneAbstracts"    in paramNames,
                    "alerts"        : "cloneAlerts"       in paramNames,
                    "participants"  : "cloneParticipants" in paramNames,
                    "evaluation"    : "cloneEvaluation"   in paramNames,
                    "managing"      : self._getUser()
                    }
        #we notify the event in case any plugin wants to add their options
        self._notify('fillCloneDict', {'options': options, 'paramNames': paramNames})
        if self._cancel:
            self._redirect( urlHandlers.UHConfClone.getURL( self._conf ) )
        elif self._confirm:
            if self._cloneType == "once" :
                newConf = self._conf.clone( self._date, options, userPerformingClone = self._aw._currentUser )
                self._redirect( urlHandlers.UHConferenceModification.getURL( newConf ) )
            elif self._cloneType == "intervals" :
                self._withIntervals(options)
            elif self._cloneType == "days" :
                self._days(options)
            else :
                self._redirect( urlHandlers.UHConfClone.getURL( self._conf ) )
        else:
            if self._cloneType == "once" :
                nbClones = 1
            elif self._cloneType == "intervals" :
                nbClones = self._withIntervals(options,0)
            elif self._cloneType == "days" :
                nbClones = self._days(options,0)
            return conferences.WPConfCloneConfirm( self, self._conf, nbClones ).display()

    def _withIntervals(self, options, confirmed=1):
        nbClones = 0
        params = self._getRequestParams()
        if params["freq"] == "day":
            inter = timedelta(int(params["period"]))
        elif params["freq"] == "week":
            inter = timedelta( 7*int(params["period"]))

        if params["intEndDateChoice"] == "until":
            date=self._date
            endDate = datetime(int(params["stdyi"]),int(params["stdmi"]),int(params["stddi"]), self._conf.getEndDate().hour,self._conf.getEndDate().minute)
            while date <= endDate:
                if confirmed:
                    self._conf.clone(date,options, userPerformingClone = self._aw._currentUser)
                nbClones += 1
                if params["freq"] == "day" or params["freq"] == "week":
                    date = date + inter
                elif params["freq"] == "month":
                    month = int(date.month) + int(params["period"])
                    year = int(date.year)
                    while month > 12:
                        month = month - 12
                        year = year + 1
                    date = datetime(year,month,int(date.day), int(date.hour), int(date.minute))
                elif params["freq"] == "year":
                    date = datetime(int(date.year)+int(params["period"]),int(date.month),int(date.day), int(date.hour), int(date.minute))

        elif params["intEndDateChoice"] == "ntimes":
            date = self._date
            i=0
            stop = int(params["numi"])
            while i < stop:
                i = i + 1
                if confirmed:
                    self._conf.clone(date,options, userPerformingClone = self._aw._currentUser)
                nbClones += 1
                if params["freq"] == "day" or params["freq"] == "week":
                    date = date + inter
                elif params["freq"] == "month":
                    month = int(date.month) + int(params["period"])
                    year = int(date.year)
                    while month > 12:
                        month = month - 12
                        year = year + 1
                    date = datetime(year,month,int(date.day), int(date.hour), int(date.minute))
                elif params["freq"] == "year":
                    date = datetime(int(date.year)+int(params["period"]),int(date.month),int(date.day), int(date.hour), int(date.minute))
        if confirmed:
            self._redirect( urlHandlers.UHCategoryDisplay.getURL( self._conf.getOwner() ) )
            return "done"
        else:
            return nbClones

    def _getFirstDay(self, date, day):
        """
        return the first day 'day' for the month of 'date'
        """
        td = datetime(int(date.year), int(date.month), 1, int(date.hour), int(date.minute))

        oneDay = timedelta(1)
        while 1:
            if td.weekday() == day:
                return td
            td = td + oneDay

    def _getOpenDay(self, date, day):
        """
        return the first open day for the month of 'date'
        """
        if day!="last": # last open day of the month
            td = datetime(int(date.year), int(date.month), int(date.day), int(date.hour), int(date.minute))
            if td.weekday() > 4:
                td = td + timedelta(7 - td.weekday())
            td += timedelta(int(day)-1)
        else:
            td = self._getLastDay(date, -1)
            if td.weekday() > 4:
                td = td - timedelta(td.weekday() - 4)
        return td

    def _getLastDay(self, date, day):
        """
        return the last day 'day' for the month of 'date'
        """
        td = datetime(int(date.year), int(date.month), 28, int(date.hour), int(date.minute))
        month=td.month
        while td.month == month:
            td += timedelta(1)
        td -= timedelta(1)
        if day==-1:
            return td
        else:
            while 1:
                if td.weekday() == day:
                    return td
                td = td - timedelta(1)

    def _days(self, options, confirmed=1):
        nbClones = 0
        params = self._getRequestParams()
        #search the first day of the month

        if params["day"] == "NOVAL":
            #self._endRequest()
            self.redirect( urlHandlers.UHConfClone.getURL( self._target ) )

        if params["daysEndDateChoice"] == "until":
            date = self._date

            endDate = datetime(int(params["stdyd"]),int(params["stdmd"]),int(params["stddd"]),self._conf.getEndDate().hour,self._conf.getEndDate().minute)

            if params["day"] == "OpenDay":
                rd = self._getOpenDay(date, params["order"])
            else:
                if params["order"] == "last":
                    rd = self._getLastDay(date, int(params["day"]))
                    if rd < date:
                        date = (date + relativedelta(months=1)).replace(day=1)
                else:
                    rd = self._getFirstDay(date, int(params["day"])) + timedelta((int(params["order"])-1)*7)
                    if rd < date:
                        date = (date + relativedelta(months=1)).replace(day=1)
            while date <= endDate:
                if params["day"] == "OpenDay":
                    od=self._getOpenDay(date,params["order"])
                    if od <= endDate:
                        if confirmed:
                            self._conf.clone(od, options, userPerformingClone = self._aw._currentUser)
                        nbClones += 1
                else:
                    if params["order"] == "last":
                        if self._getLastDay(date,int(params["day"])) <= endDate:
                            if confirmed:
                                self._conf.clone(self._getLastDay(date,int(params["day"])), options, userPerformingClone = self._aw._currentUser)
                            nbClones += 1
                    else:
                        if self._getFirstDay(date, int(params["day"])) + timedelta((int(params["order"])-1)*7) <= endDate:
                            if confirmed:
                                self._conf.clone(self._getFirstDay(date, int(params["day"]))+ timedelta((int(params["order"])-1)*7), options, userPerformingClone = self._aw._currentUser)
                            nbClones += 1
                month = int(date.month) + int(params["monthPeriod"])
                year = int(date.year)
                while month > 12:
                    month = month - 12
                    year = year + 1
                date = datetime(year,month,1, int(date.hour), int(date.minute))

        elif params["daysEndDateChoice"] == "ntimes":

            date = self._date
            if params["day"] == "OpenDay":
                rd = self._getOpenDay(date,params["order"])
            else:
                if params["order"] == "last":
                    rd = self._getLastDay(date, int(params["day"]))
                    if rd < date:
                        date = (date + relativedelta(months=1)).replace(day=1)
                else:
                    rd = self._getFirstDay(date, int(params["day"])) + timedelta((int(params["order"])-1)*7)
                    if rd < date:
                        date = (date + relativedelta(months=1)).replace(day=1)

            i=0
            stop = int(params["numd"])
            while i < stop:
                i = i + 1
                if params["day"] == "OpenDay":
                    if confirmed:
                        self._conf.clone(self._getOpenDay(date, params["order"]), options, userPerformingClone = self._aw._currentUser)
                    nbClones += 1
                else:
                    if params["order"] == "last":
                        if confirmed:
                            self._conf.clone(self._getLastDay(date,int(params["day"])), options, userPerformingClone = self._aw._currentUser)
                        nbClones += 1
                    else:
                        if confirmed:
                            self._conf.clone(self._getFirstDay(date, int(params["day"]))+ timedelta((int(params["order"])-1)*7), options, userPerformingClone = self._aw._currentUser)
                        nbClones += 1
                month = int(date.month) + int(params["monthPeriod"])
                year = int(date.year)
                while month > 12:
                    month = month - 12
                    year = year + 1
                date = datetime(year,month,int(date.day), int(date.hour), int(date.minute))
        if confirmed:
            self._redirect( urlHandlers.UHCategoryDisplay.getURL( self._conf.getOwner() ) )
        else:
            return nbClones




####################################################################################

class RHConfDisplayAlarm( RHConferenceModifBase ):

    def _process( self ):
        p = conferences.WPConfDisplayAlarm( self, self._conf )
        return p.display()

class RHConfAddAlarm( RHConferenceModifBase ):

    def _process( self ):
        p = conferences.WPConfAddAlarm( self, self._conf )
        return p.display()

class RHCreateAlarm( RoomBookingDBMixin, RHConferenceModifBase ):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        if not params.has_key("fromAddr") or params.get("fromAddr","")=="":
            raise FormValuesError( _("""Please choose a "FROM" address for this alarm"""))
        self._fromAddr=params.get("fromAddr")

        if not params.has_key("toAllParticipants") and (not params.has_key("defineRecipients")
                                                        or (params.has_key("defineRecipients") and params.get("Emails","")=="")):
            raise FormValuesError( _("""Please select the checkbox 'Send to all participants' or 'Define recipients' with a list of emails."""))
        self._toAllParticipants = params.get("toAllParticipants", False)
        self._defineRecipients = params.get("defineRecipients", False)
        self._emails = params.get("Emails","")

        self._dateType = params.get("dateType", "")
        self._year = int(params["year"])
        self._month = int(params["month"])
        self._day = int(params["day"])
        self._hour = int(params["hour"])
        self._minute = int(params["minute"])
        self._timeBefore = int(params.get("timeBefore", 0))
        if self._dateType == "2" and self._timeBefore <= 0:
            raise FormValuesError(_("Time before the beginning of the event should be bigger than zero"))
        self._timeTypeBefore = params["timeTypeBefore"]
        self._note = params.get("note", "")
        self._includeConf = params.get("includeConf", None)
        self._alarmId = params.get("alarmId", None)
        self._testAlarm = False

    def _initializeAlarm(self, dryRun=False):
        if dryRun:  # sending now
            dtStart = timezoneUtils.nowutc()
            relative = None
        else:
            if self._dateType == "1":  # given date
                dtStart = timezone(self._conf.getTimezone()).localize(datetime(self._year,
                                                                              self._month,
                                                                              self._day,
                                                                              self._hour,
                                                                              self._minute)).astimezone(timezone('UTC'))
                relative = None
            elif self._dateType == "2":  # N days/hours before the event
                if self._timeTypeBefore == "days":
                    delta = timedelta(days=self._timeBefore)
                elif self._timeTypeBefore == "hours":
                    delta = timedelta(0, self._timeBefore * 3600)
                dtStart = self._target.getStartDate() - delta
                relative = delta
            else:
                raise MaKaCError(_("Wrong value has been choosen for 'when to send the alarm'"))

        if self._alarmId:
            al = self._conf.getAlarmById(self._alarmId)
            c = Client()
            if dryRun:
                c.dequeue(al)
            else:
                c.moveTask(al, dtStart)
            al.setRelative(relative)
        else:
            al = self._conf.newAlarm(relative or dtStart, enqueue=not dryRun)

        al.setToAddrList([])
        if(self._defineRecipients or self._testAlarm):
            for addr in self._emails.split(","):
                addr = addr.strip()
                if addr:
                    al.addToAddr(addr)

        al.setFromAddr(self._fromAddr)

        if self._includeConf and self._includeConf == "1":
            al.setConfSummary(True)
        else:
            al.setConfSummary(False)

        al.setSubject("Event reminder: %s"%self._conf.getTitle())

        al.setNote(self._note)

        al.setToAllParticipants(self._toAllParticipants)
        self._al = al

class RHConfSendAlarmNow( RHCreateAlarm ):

    def _checkParams( self, params ):
        RHCreateAlarm._checkParams( self, params )

        self._initializeAlarm(dryRun = True)

    def _process( self ):
        RHCreateAlarm._process(self)
        if self._al:
            self._al.run(check = False)
            self._al.setStartedOn(timezoneUtils.nowutc())
            self._al.setEndedOn(timezoneUtils.nowutc())
        self._redirect( urlHandlers.UHConfDisplayAlarm.getURL( self._target ) )

class RHConfSaveAlarm( RHCreateAlarm ):

    def _checkParams( self, params ):
        RHCreateAlarm._checkParams( self, params )

        if not params.has_key("dateType") or params.get("dateType","")=="":
            raise FormValuesError(_("Please choose when to send this alarm"))

        self._initializeAlarm()

    def _process(self):
        self._redirect( urlHandlers.UHConfDisplayAlarm.getURL( self._target ) )

class RHConfDeleteAlarm( RHAlarmBase ):

    def _process(self):
        if self._alarm.getEndedOn():
            raise MaKaCError(_("The alarm can not be deleted"))
        self._alarm.delete()
        self._redirect( urlHandlers.UHConfDisplayAlarm.getURL( self._conf ) )


class RHConfModifyAlarm( RHAlarmBase ):

    def _process(self):
        return conferences.WPConfModifyAlarm( self, self._conf, self._alarm ).display()


class RHConfModifProgram( RHConferenceModifBase ):

    def _process( self ):
        p = conferences.WPConfModifProgram( self, self._target )
        return p.display()


class RHConfAddTrack( RHConferenceModifBase ):

    def _process( self ):
        p = conferences.WPConfAddTrack( self, self._target )
        return p.display()


class RHConfPerformAddTrack( RHConferenceModifBase ):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._cancel = params.has_key("cancel")

    def _process( self ):
        if self._cancel:
            self._redirect( urlHandlers.UHConfModifProgram.getURL( self._conf ) )
        else:
            t = self._conf.newTrack()
            params = self._getRequestParams()
            t.setTitle(params["title"])
            t.setDescription(params["description"])
            # Filtering criteria: by default make new contribution type checked
            dct = session.setdefault("ContributionFilterConf%s" % self._conf.getId(), {})
            if 'tracks' in dct:
                #Append the new type to the existing list
                newDict = dct['tracks'][:]
                newDict.append(t.getId())
                dct['tracks'] = newDict[:]
            else:
                #Create a new entry for the dictionary containing the new type
                dct['tracks'] = [t.getId()]
            session.modified = True
            self._redirect( urlHandlers.UHConfModifProgram.getURL( self._conf ) )

class RHConfDelTracks( RHConferenceModifBase ):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._trackList = []
        for id in self._normaliseListParam( params.get("selTracks", []) ):
            self._trackList.append( self._conf.getTrackById( id ) )

    def _process( self ):
        for track in self._trackList:
            self._conf.removeTrack( track )
        self._redirect( urlHandlers.UHConfModifProgram.getURL( self._conf ) )


class RHProgramTrackUp(RHConferenceModifBase):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._track=self._target.getTrackById(params.get("trackId",""))

    def _process( self ):
        self._disableCaching()
        self._target.moveUpTrack(self._track)
        self._redirect(urlHandlers.UHConfModifProgram.getURL(self._conf))


class RHProgramTrackDown(RHConferenceModifBase):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._track=self._target.getTrackById(params.get("trackId",""))

    def _process( self ):
        self._disableCaching()
        self._target.moveDownTrack(self._track)
        self._redirect(urlHandlers.UHConfModifProgram.getURL(self._conf))

class CFAEnabled(object):
    @staticmethod
    def checkEnabled(request):
        """ Returns true if abstracts has been enabled
            Otherwise, throws an exception
        """
        if request._conf.hasEnabledSection("cfa"):
            return True
        else:
            raise MaKaCError( _("You cannot access this option because \"Abstracts\" was disabled"))

class RHConfModifCFABase(RHConferenceModifBase):

    def _checkProtection(self):
        RHConferenceModifBase._checkProtection(self)
        CFAEnabled.checkEnabled(self)

class RHConfModifCFA(RHConfModifCFABase):

    def _process( self ):
        p = conferences.WPConfModifCFA( self, self._target )
        return p.display()


class RHConfModifCFAPreview(RHConfModifCFABase):

    def _process( self ):
        p = conferences.WPConfModifCFAPreview( self, self._target )
        return p.display()


class RHConfModifCFAStatus( RHConfModifCFABase ):

    def _checkParams( self, params ):
        RHConfModifCFABase._checkParams( self, params )
        self._newStatus = params["changeTo"]

    def _process( self ):
        if self._newStatus == "True":
            self._conf.getAbstractMgr().activeCFA()
        else:
            self._conf.getAbstractMgr().desactiveCFA()
        self._redirect( urlHandlers.UHConfModifCFA.getURL( self._conf ) )


class RHConfModifCFASwitchMultipleTracks( RHConfModifCFABase ):

    def _process( self ):
        self._conf.getAbstractMgr().setMultipleTracks(not self._conf.getAbstractMgr().getMultipleTracks())
        self._redirect( urlHandlers.UHConfModifCFA.getURL( self._conf ) )

class RHConfModifCFAMakeTracksMandatory( RHConfModifCFABase ):

    def _process( self ):
        self._conf.getAbstractMgr().setTracksMandatory(not self._conf.getAbstractMgr().areTracksMandatory())
        self._redirect( urlHandlers.UHConfModifCFA.getURL( self._conf ) )


class RHConfModifCFASwitchAttachFiles( RHConfModifCFABase ):

    def _process( self ):
        self._conf.getAbstractMgr().setAllowAttachFiles(not self._conf.getAbstractMgr().canAttachFiles())
        self._redirect( urlHandlers.UHConfModifCFA.getURL( self._conf ) )


class RHConfModifCFASwitchShowSelectAsSpeaker( RHConfModifCFABase ):

    def _process( self ):
        self._conf.getAbstractMgr().setShowSelectAsSpeaker(not self._conf.getAbstractMgr().showSelectAsSpeaker())
        self._redirect( urlHandlers.UHConfModifCFA.getURL( self._conf ) )

class RHConfModifCFASwitchSelectSpeakerMandatory( RHConfModifCFABase ):

    def _process( self ):
        self._conf.getAbstractMgr().setSelectSpeakerMandatory(not self._conf.getAbstractMgr().isSelectSpeakerMandatory())
        self._redirect( urlHandlers.UHConfModifCFA.getURL( self._conf ) )

class RHConfModifCFASwitchShowAttachedFilesContribList( RHConfModifCFABase ):

    def _process( self ):
        self._conf.getAbstractMgr().setSwitchShowAttachedFilesContribList(not self._conf.getAbstractMgr().showAttachedFilesContribList())
        self._redirect( urlHandlers.UHConfModifCFA.getURL( self._conf ) )


class RHCFADataModification( RHConfModifCFABase ):

    def _process( self ):
        p = conferences.WPCFADataModification( self, self._target )
        return p.display()


class RHCFAPerformDataModification( RHConfModifCFABase ):

    def _checkParams( self, params ):
        RHConfModifCFABase._checkParams( self, params )
        self._cancel = params.has_key("cancel")
        self._modifDL = None
        mDay = str( params.get( "mDay", "" ) ).strip()
        mMonth = str( params.get( "mMonth", "" ) ).strip()
        mYear = str( params.get( "mYear", "" ) ).strip()
        if mDay != "" and mMonth !="" and mYear != "":
            self._modifDL = datetime( int(mYear), int(mMonth), int(mDay) )

    def _process( self ):
        if self._cancel:
            self._redirect( urlHandlers.UHConfModifCFA.getURL( self._conf ) )
        else:
            abMgr = self._conf.getAbstractMgr()
            params = self._getRequestParams()

            abMgr.setStartSubmissionDate(datetime(int(params["sYear"]), int(params["sMonth"]), int(params["sDay"])))
            abMgr.setEndSubmissionDate(datetime(int(params["eYear"]), int(params["eMonth"]), int(params["eDay"])))
            try:
                sDate = datetime(int(params["sYear"]), int(params["sMonth"]), int(params["sDay"]))
            except ValueError, e:
                raise FormValuesError("The start date you have entered is not correct: %s" % e, "Abstracts")
            try:
                eDate = datetime(int(params["eYear"]), int(params["eMonth"]), int(params["eDay"]))
            except ValueError, e:
                raise FormValuesError("The end date you have entered is not correct: %s" % e, "Abstracts")
            if eDate < sDate:
                raise FormValuesError("End date can't be before start date!", "Abstracts")
            try:
                mDate = None
                if params["mYear"] or params["mMonth"] or params["mDay"]:
                    mDate = datetime(int(params["mYear"]), int(params["mMonth"]), int(params["mDay"]))
            except ValueError, e:
                raise FormValuesError("The modification end date you have entered is not correct: %s" % e, "Abstracts")
            if mDate is not None and mDate < eDate:
                raise FormValuesError("Modification end date must be after end date!", "Abstracts")

            abMgr.setAnnouncement(params["announcement"])
            abMgr.setModificationDeadline(self._modifDL)
            abMgr.getSubmissionNotification().setToList(utils.getEmailList(params.get("toList", "")))
            abMgr.getSubmissionNotification().setCCList(utils.getEmailList(params.get("ccList", "")))
            self._redirect(urlHandlers.UHConfModifCFA.getURL(self._conf))


class AbstractStatusFilter( filters.FilterField ):
    """Contains the filtering criteria for the status of an abstract.

        Implements the logic to determine whether abstracts are within a list
        of abstract status. Objects of this class will keep a list of status
        names; then an abstract will satisfy the filter if it is in an abstract
        which name is included in the list of values.

        Inherits from: AbstractFilterField

        Attributes:
            _values -- (list) List of abstract status names; if the name of the
                current status of an abstract is included in this list, the
                abstract will satisfy the filter field.
            _showNoValue -- (bool) Not used for this filter field.
    """
    _id = "status"

    def satisfies( self, abstract ):
        if len(AbstractStatusList.getInstance().getStatusList()) == len(self._values):
            return True
        else:
            status = AbstractStatusList.getInstance().getId( abstract.getCurrentStatus().__class__ )
            return status in self._values

    def needsToBeApplied(self):
        for s in AbstractStatusList.getStatusList():
            if AbstractStatusList.getInstance().getId(s) not in self._values:
                return True
        return False


class AbstractFilterCriteria(filters.FilterCriteria):
    """
    """
    _availableFields = {
        abstractFilters.TrackFilterField.getId(): \
                                    abstractFilters.TrackFilterField, \
        abstractFilters.ContribTypeFilterField.getId(): \
                                    abstractFilters.ContribTypeFilterField, \
        AbstractStatusFilter.getId() : AbstractStatusFilter, \
        abstractFilters.CommentFilterField.getId(): \
                                    abstractFilters.CommentFilterField, \
        abstractFilters.AccContribTypeFilterField.getId():\
                        abstractFilters.AccContribTypeFilterField,
        abstractFilters.AccTrackFilterField.getId():\
                        abstractFilters.AccTrackFilterField }


class _AbstractStatusSF( filters.SortingField ):
    _id = "status"

    def compare( self, a1, a2 ):
        a1Stat, a2Stat = a1.getCurrentStatus(), a2.getCurrentStatus()
        if a1Stat == a2Stat:
            return 0
        a1StatLabel = AbstractStatusList.getInstance().getCaption( a1Stat.__class__ )
        a2StatLabel = AbstractStatusList.getInstance().getCaption( a2Stat.__class__ )
        return cmp( a1StatLabel, a2StatLabel )


class _AbstractIdSF( filters.SortingField ):
    _id = "number"

    def compare( self, a1, a2 ):
        try:
            a = int(a1.getId())
            b = int(a2.getId())
        except:
            a = a1.getId()
            b = a2.getId()
        return cmp( a, b )

class _AbstractRatingSF( filters.SortingField ):
    _id = "rating"

    def compare( self, a1, a2 ):
        a = a1.getRating()
        b = a2.getRating()
        # check if the rating is none because the abstract has no judgement
        if a == None:
            a = -1.0
        if b == None:
            b = -1.0
        return cmp( a, b )

class _AbstractTrackSF( filters.SortingField ):
    _id = "track"

    def compare( self, a1, a2 ):
        trackList1 = a1.getTrackList()
        trackList2 = a2.getTrackList()
        # check if there is track assignement for the abstract and get the list of ids if needed
        if len(trackList1) == 0:
            a = [-1]
        else:
            a = [track.getId() for track in trackList1]
        if len(trackList2) == 0:
            b = [-1]
        else:
            b = [track.getId() for track in trackList2]
        return cmp( a, b )

class AbstractSortingCriteria( filters.SortingCriteria ):
    """
    """
    _availableFields = {
        abstractFilters.ContribTypeSortingField.getId(): \
                                abstractFilters.ContribTypeSortingField, \
        _AbstractTrackSF.getId(): _AbstractTrackSF, \
        _AbstractStatusSF.getId(): _AbstractStatusSF, \
        _AbstractIdSF.getId(): _AbstractIdSF, \
        _AbstractRatingSF.getId(): _AbstractRatingSF, \
        abstractFilters.SubmissionDateSortingField.getId() : \
                                    abstractFilters.SubmissionDateSortingField, \
        abstractFilters.ModificationDateSortingField.getId() : \
                                    abstractFilters.ModificationDateSortingField
                                     }


class RHAbstractList(RHConfModifCFABase):
    _uh = urlHandlers.UHConfAbstractManagment

    def _resetFilters( self, sessionData ):
        """
        Brings the filter data to a consistent state (websession),
        marking everything as "checked"
        """

        sessionData["track"] = sessionData["acc_track"] = [track.getId() for track in self._conf.getTrackList()]
        sessionData["type"] = sessionData["acc_type"] = [ct.getId() for ct in self._conf.getContribTypeList()]
        abstractStatusList = AbstractStatusList.getInstance()
        sessionData["status"] = map(lambda status: abstractStatusList.getId( status ), abstractStatusList.getStatusList())
        sessionData['authSearch'] = ""

        sessionData["trackShowNoValue"] = True
        sessionData["typeShowNoValue"] = True
        sessionData["accTypeShowNoValue"] = True
        sessionData["accTrackShowNoValue"] = True
        sessionData["trackShowMultiple"] = False
        sessionData.pop("comment", None)

        return sessionData

    def _updateFilters( self, sessionData, params ):
        """
        Updates the filter parameters in the websession with those
        coming from the HTTP request
        """
        sessionData['track'] = []
        sessionData['acc_track'] = []
        sessionData['type'] = []
        sessionData['acc_type'] = []
        sessionData['status'] = []
        sessionData['authSearch'] = ""

        sessionData.update(params)

        sessionData['track'] = utils.normalizeToList(sessionData.get("track"))
        sessionData['status'] = utils.normalizeToList(sessionData.get("status"))
        sessionData['acc_track'] = utils.normalizeToList(sessionData.get("acc_track"))

        # update these elements in the session so that the parameters that are
        # passed are always taken into account (sessionData.update is not
        # enough, since the elements that are ommitted in params would just be
        # ignored

        sessionData['trackShowNoValue'] = params.has_key('trackShowNoValue')
        sessionData['trackShowMultiple'] = params.has_key("trackShowMultiple")
        sessionData['accTrackShowNoValue'] = params.has_key("accTrackShowNoValue")
        sessionData['typeShowNoValue'] = params.has_key('typeShowNoValue')
        sessionData['accTypeShowNoValue'] = params.has_key('accTypeShowNoValue')
        if params.has_key("comment"):
            sessionData['comment'] = ""
        elif sessionData.has_key("comment"):
            del sessionData['comment']
        return sessionData

    def _buildFilteringCriteria(self, sessionData):
        """
        Creates the Filtering Criteria object, without changing the existing
        session data (sessionData is cloned, not directly changed)
        """
        sessionCopy = sessionData.copy()

        # Build the filtering criteria
        filterCrit = AbstractFilterCriteria(self._conf, sessionCopy)

        filterCrit.getField("track").setShowNoValue(sessionCopy.get("trackShowNoValue"))
        filterCrit.getField("track").setOnlyMultiple(sessionCopy.get("trackShowMultiple"))
        filterCrit.getField("acc_track").setShowNoValue(sessionCopy.get("accTrackShowNoValue"))
        filterCrit.getField("type").setShowNoValue(sessionCopy.get("typeShowNoValue"))
        filterCrit.getField("acc_type").setShowNoValue(sessionCopy.get("accTypeShowNoValue"))

        return filterCrit

    def _checkAction( self, params, filtersActive, sessionData, operation ):
        """
        Decides what to do with the request parameters, depending
        on the type of operation that is requested
        """
        # user chose to reset the filters
        if operation ==  'resetFilters':
            self._filterUsed = False
            sessionData = self._resetFilters(sessionData)

        # user set the filters
        elif operation ==  'setFilters':
            self._filterUsed = True
            sessionData = self._updateFilters(sessionData, params)

        # user has changed the display options
        elif operation == 'setDisplay':
            self._filterUsed = filtersActive
            sessionData['disp'] = params.get('disp',[])

        # session is empty (first time)
        elif not filtersActive:
            self._filterUsed = False
            sessionData = self._resetFilters(sessionData)
        else:
            self._filterUsed = True

        # preserve the order and sortBy parameters, whatever happens
        sessionData['order'] = params.get('order', 'down')
        sessionData['sortBy'] = params.get('sortBy', 'number')

        return sessionData

    def _checkParams( self, params ):
        RHConfModifCFABase._checkParams( self, params )

        operationType = params.get('operationType')

        # session data
        sessionData = session.get('abstractFilterAndSortingConf%s' % self._conf.getId())

        # check if there is information already
        # set in the session variables
        if sessionData:
            # work on a copy
            sessionData = sessionData.copy()
            filtersActive =  sessionData['filtersActive']
        else:
            # set a default, empty dict
            sessionData = {}
            filtersActive = False

        if 'resetFilters' in params:
            operation = 'resetFilters'
        elif operationType == 'filter':
            operation =  'setFilters'
        elif operationType == 'display':
            operation = 'setDisplay'
        else:
            operation = None

        sessionData = self._checkAction(params, filtersActive, sessionData, operation)

        # Maintain the state abotu filter usage
        sessionData['filtersActive'] = self._filterUsed

        # Save the web session
        session['abstractFilterAndSortingConf%s' % self._conf.getId()] = sessionData

        self._filterCrit = self._buildFilteringCriteria(sessionData)

        self._sortingCrit = AbstractSortingCriteria( [sessionData.get( "sortBy", "number" ).strip()] )

        self._order = sessionData.get("order","down")

        self._msg = sessionData.get("directAbstractMsg","")
        self._authSearch = sessionData.get("authSearch", "")

        self._display = utils.normalizeToList(sessionData.get("disp",[]))

    def _process( self ):
        p = conferences.WPConfAbstractList(self,self._target, self._msg, self._filterUsed)
        return p.display( filterCrit = self._filterCrit,
                            sortingCrit = self._sortingCrit,
                            authSearch=self._authSearch, order=self._order,
                            display = self._display)

class RHAbstractsActions:
    """
    class to select the action to do with the selected abstracts
    """
    def __init__(self, req):
        assert req is None

    def process(self, params):
        if params.has_key("newAbstract"):
            return RHNewAbstract(None).process(params)
        elif params.has_key("pdf"):
            return RHAbstractsToPDF(None).process(params)
        elif params.has_key("excel"):
            return RHAbstractsListToExcel(None).process(params)
        elif params.has_key("xml"):
            return RHAbstractsToXML(None).process(params)
        elif params.has_key("auth"):
            return RHAbstractsParticipantList(None).process(params)
        elif params.has_key("merge"):
            return RHAbstractsMerge(None).process(params)
        elif params.has_key("acceptMultiple"):
            return RHAbstractManagmentAcceptMultiple(None).process(params)
        elif params.has_key("rejectMultiple"):
            return RHAbstractManagmentRejectMultiple(None).process(params)
        elif params.has_key("PKGA"):
            return RHMaterialPackageAbstract(None).process(params)
        return "no action to do"


class RHAbstractsMerge(RHConfModifCFABase):

    def _checkParams(self, params):
        RHConfModifCFABase._checkParams(self, params)
        self._abstractIds = normaliseListParam(params.get("abstracts", []))
        self._targetAbsId = params.get("targetAbstract", "")
        self._inclAuthors = "includeAuthors" in params
        self._doNotify = "notify" in params
        self._comments = params.get("comments", "")
        self._action = ""
        if "CANCEL" in params:
            self._action = "CANCEL"
        elif "OK" in params:
            self._action = "MERGE"
            self._abstractIds = params.get("selAbstracts", "").split(",")
        else:
            self._doNotify = True

    def _process(self):
        errorList = []

        if self._action == "CANCEL":
            self._redirect(
                urlHandlers.UHConfAbstractManagment.getURL(self._target))
            return
        elif self._action == "MERGE":
            absMgr = self._target.getAbstractMgr()
            if len(self._abstractIds) == 0:
                errorList.append(
                    _("No ABSTRACT TO BE MERGED has been specified"))
            else:
                self._abstracts = []
                for id in self._abstractIds:
                    abst = absMgr.getAbstractById(id)
                    if abst is None:
                        errorList.append(_("ABSTRACT TO BE MERGED ID '%s' is not valid") % (id))
                    else:
                        statusKlass = abst.getCurrentStatus().__class__
                        if statusKlass in (review.AbstractStatusAccepted,
                                           review.AbstractStatusRejected,
                                           review.AbstractStatusWithdrawn,
                                           review.AbstractStatusDuplicated,
                                           review.AbstractStatusMerged):
                            label = AbstractStatusList.getInstance(
                            ).getCaption(statusKlass)
                            errorList.append(_("ABSTRACT TO BE MERGED %s is in status which does not allow to merge (%s)") % (abst.getId(), label.upper()))
                        self._abstracts.append(abst)
            if self._targetAbsId == "":
                errorList.append(_("Invalid TARGET ABSTRACT ID"))
            else:
                if self._targetAbsId in self._abstractIds:
                    errorList.append(_("TARGET ABSTRACT ID is among the ABSTRACT IDs TO BE MERGED"))
                self._targetAbs = absMgr.getAbstractById(self._targetAbsId)
                if self._targetAbs is None:
                    errorList.append(_("Invalid TARGET ABSTRACT ID"))
                else:
                    statusKlass = self._targetAbs.getCurrentStatus().__class__
                    if statusKlass in (review.AbstractStatusAccepted,
                                       review.AbstractStatusRejected,
                                       review.AbstractStatusWithdrawn,
                                       review.AbstractStatusMerged,
                                       review.AbstractStatusDuplicated):
                        label = AbstractStatusList.getInstance(
                        ).getInstance().getCaption(statusKlass)
                        errorList.append(_("TARGET ABSTRACT is in status which does not allow to merge (%s)") % label.upper())
            if len(errorList) == 0:
                for abs in self._abstracts:
                    abs.mergeInto(self._getUser(), self._targetAbs,
                                  mergeAuthors=self._inclAuthors, comments=self._comments)
                    if self._doNotify:
                        abs.notify(EmailNotificator(), self._getUser())
                return self._redirect(urlHandlers.UHAbstractManagment.getURL(self._targetAbs))
        p = conferences.WPModMergeAbstracts(self, self._target)
        return p.display(absIdList=self._abstractIds,
                         targetAbsId=self._targetAbsId,
                         inclAuth=self._inclAuthors,
                         comments=self._comments,
                         errorMsgList=errorList,
                         notify=self._doNotify)


#Base class for multi abstract management
class RHAbstractManagmentMultiple( RHConferenceModifBase ):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams(self, params)
        abstractIds = params.get("abstracts",[])
        abMgr = self._conf.getAbstractMgr()
        self._abstracts = []
        #if single abstract id is sent it's not a list so it shouldn't be iterated
        if isinstance(abstractIds, types.ListType):
            for id in abstractIds:
                self._abstracts.append(abMgr.getAbstractById(id))
        else:
            self._abstracts.append(abMgr.getAbstractById(abstractIds))
        self._warningShown=params.has_key("confirm")
        self._comments = params.get("comments", "")
        self._doNotify=params.has_key("notify")

    #checks if notification email template is defined for all selected abstracts
    #returns List of abstracts which doesn't have required template
    def _checkNotificationTemplate(self, statusKlass):
        from MaKaC.webinterface.rh.abstractModif import _AbstractWrapper

        if statusKlass == review.AbstractStatusAccepted:
            cType=self._conf.getContribTypeById(self._typeId)

        abstractsWithMissingTemplate = []
        for abstract in self._abstracts:
            if statusKlass == review.AbstractStatusAccepted:
                status=statusKlass(abstract,None,self._track,cType)
            elif statusKlass == review.AbstractStatusRejected:
                status=statusKlass(abstract,None, None)
            else: # In case we pass an improper Status
                abstractsWithMissingTemplate.append(abstract)
                continue
            wrapper=_AbstractWrapper(status)
            if abstract.getOwner().getNotifTplForAbstract(wrapper) is None:
                abstractsWithMissingTemplate.append(abstract)
        return abstractsWithMissingTemplate

    #checks the status of selected abstracts
    #returns list of abstracts with improper status
    def _checkStatus(self):
        improperAbstracts = []
        for abstract in self._abstracts:
            status = abstract.getCurrentStatus()
            if not isinstance(status, AbstractStatusSubmitted) and \
               not isinstance(status, AbstractStatusProposedToAccept) and \
               not isinstance(status, AbstractStatusProposedToReject):
                improperAbstracts.append(abstract)
        return improperAbstracts


class RHAbstractManagmentAcceptMultiple( RHAbstractManagmentMultiple ):

    def _checkParams( self, params ):
        RHAbstractManagmentMultiple._checkParams(self, params)
        self._accept = params.get("accept", None)
        self._track=self._conf.getTrackById(params.get("track", ""))
        self._session=self._conf.getSessionById(params.get("session", ""))
        self._typeId = params.get("type", "")

    def _process( self ):
        if self._abstracts != []:
            improperAbstracts = self._checkStatus()
            if improperAbstracts == []:
                if self._accept:
                    improperTemplates = self._checkNotificationTemplate(review.AbstractStatusAccepted)
                    if self._doNotify and not self._warningShown and  improperTemplates != []:
                        raise FormValuesError("""The abstracts with the following IDs can not be automatically
                                                 notified: %s. Therefore, none of your request has been processed;
                                                 go back, uncheck the relevant abstracts and try again."""%(", ".join(map(lambda x:x.getId(),improperTemplates))))
                    cType=self._conf.getContribTypeById(self._typeId)
                    for abstract in self._abstracts:
                        abstract.accept(self._getUser(),self._track,cType,self._comments,self._session)
                        if self._doNotify:
                            n=EmailNotificator()
                            abstract.notify(n,self._getUser())
                    self._redirect(urlHandlers.UHConfAbstractManagment.getURL(self._conf))
                else:
                    p = abstracts.WPAbstractManagmentAcceptMultiple( self, self._abstracts )
                    return p.display( **self._getRequestParams() )
            else:
                raise FormValuesError("""The abstracts with the following IDs cannot be accepted because of their
                                current status: %s. Therefore, none of your request has been processed;
                                go back, uncheck the relevant abstracts and try again."""%(", ".join(map(lambda x:x.getId(),improperAbstracts))))
        else:
            raise FormValuesError("No abstracts selected")


class RHAbstractManagmentRejectMultiple( RHAbstractManagmentMultiple ):

    def _checkParams( self, params ):
        RHAbstractManagmentMultiple._checkParams(self, params)
        self._reject = params.get("reject", None)
        self._comments = params.get("comments", "")
        self._doNotify=params.has_key("notify")
        self._warningShown=params.has_key("confirm")

    def _process( self ):
        if self._abstracts != []:
            improperAbstracts = self._checkStatus()
            if improperAbstracts == []:
                if self._reject:
                    improperTemplates = self._checkNotificationTemplate(review.AbstractStatusRejected)
                    if self._doNotify and not self._warningShown and  improperTemplates != []:
                        raise FormValuesError("""The abstracts with the following IDs can not be automatically
                                                 notified: %s. Therefore, none of your request has been processed;
                                                 go back, uncheck the relevant abstracts and try again."""%(", ".join(map(lambda x:x.getId(),improperTemplates))))
                    for abstract in self._abstracts:
                        abstract.reject(self._getUser(), self._comments)
                        if self._doNotify:
                            n=EmailNotificator()
                            abstract.notify(n,self._getUser())
                    self._redirect(urlHandlers.UHConfAbstractManagment.getURL(self._conf))
                else:
                    p = abstracts.WPAbstractManagmentRejectMultiple( self, self._abstracts )
                    return p.display( **self._getRequestParams() )
            else:
                raise FormValuesError("""The abstracts with the following IDs cannot be rejected because of their
                                current status: %s. Therefore, none of your request has been processed;
                                go back, uncheck the relevant abstracts and try again."""%(", ".join(map(lambda x:x.getId(),improperAbstracts))))
        else:
            raise FormValuesError("No abstracts selected")

class RHAbstractSendNotificationMail(RHConfModifCFABase):

    def _checkParams( self, params ):
        RHConfModifCFABase._checkParams( self, params )
        notifTplId = params.get("notifTpl", "")
        self._notifTpl = self._conf.getAbstractMgr().getNotificationTplById(notifTplId)
        self._abstractIds = normaliseListParam( params.get("abstracts", []) )
        self._abstracts = []
        abMgr = self._conf.getAbstractMgr()
        for id in self._abstractIds:
            self._abstracts.append(abMgr.getAbstractById(id))

    def _process( self ):
        p = conferences.WPAbstractSendNotificationMail(self, self._conf, count )
        return p.display()


class RHAbstractsToPDF(RHConfModifCFABase):

    def _checkParams( self, params ):
        RHConfModifCFABase._checkParams( self, params )
        self._abstractIds = normaliseListParam( params.get("abstracts", []) )

    def _process(self):
        tz = self._conf.getTimezone()
        if not self._abstractIds:
            return _("No abstract to print")

        pdf = ConfManagerAbstractsToPDF(self._conf, self._abstractIds, tz=tz)
        return send_file('Abstracts.pdf', pdf.generate(), 'PDF')


class RHAbstractsToXML(RHConfModifCFABase):

    def _checkParams( self, params ):
        RHConfModifCFABase._checkParams( self, params )
        self._abstractIds = normaliseListParam( params.get("abstracts", []) )
        self._abstracts = []
        abMgr = self._conf.getAbstractMgr()
        for id in self._abstractIds:
            #if abMgr.getAbstractById(id).canView( self._aw ):
            self._abstracts.append(abMgr.getAbstractById(id))

    def _process(self):
        x = XMLGen()

        x.openTag("AbstractBook")
        x.writeTag("Conference", self._target.getConference().getTitle())
        for abstract in self._abstracts:
            x.openTag("abstract")
            x.writeTag("Id", abstract.getId())
            x.writeTag("Title", abstract.getTitle())
            x.writeTag("Content", abstract.getField("content"))
            for f in self._conf.getAbstractMgr().getAbstractFieldsMgr().getFields():
                id = f.getId()
                x.writeTag("field",abstract.getField(id),[("id",id)])
            l = []
            for au in abstract.getAuthorList():
                if abstract.isPrimaryAuthor(au):
                    x.openTag("PrimaryAuthor")
                    x.writeTag("FirstName", au.getFirstName())
                    x.writeTag("FamilyName", au.getSurName())
                    x.writeTag("Email", au.getEmail())
                    x.writeTag("Affiliation", au.getAffiliation())
                    x.closeTag("PrimaryAuthor")
                else:
                    l.append(au)

            for au in l:
                x.openTag("Co-Author")
                x.writeTag("FirstName", au.getFirstName())
                x.writeTag("FamilyName", au.getSurName())
                x.writeTag("Email", au.getEmail())
                x.writeTag("Affiliation", au.getAffiliation())
                x.closeTag("Co-Author")

            for au in abstract.getSpeakerList():
                x.openTag("Speaker")
                x.writeTag("FirstName", au.getFirstName ())
                x.writeTag("FamilyName", au.getSurName())
                x.writeTag("Email", au.getEmail())
                x.writeTag("Affiliation", au.getAffiliation())
                x.closeTag("Speaker")

            #To change for the new contribution type system to:
            #x.writeTag("ContributionType", abstract.getContribType().getName())
            if abstract.getContribType() <> None:
                x.writeTag("ContributionType", abstract.getContribType().getName())
            else:
                x.writeTag("ContributionType", None)
            #x.writeTag("ContributionType", abstract.getContribType())

            for t in abstract.getTrackList():
                x.writeTag("Track", t.getTitle())

            x.closeTag("abstract")

        x.closeTag("AbstractBook")

        return send_file('Abstracts.xml', StringIO(x.getXml()), 'XML')


#-------------------------------------------------------------------------------------

class RHAbstractsListToExcel(RHConfModifCFABase):

    def _checkParams( self, params ):
        RHConfModifCFABase._checkParams( self, params )
        self._abstracts = normaliseListParam( params.get("abstracts", []) )
        self._display = self._normaliseListParam(params.get("disp",[]))

    def _process( self ):
        abstractList = []
        for abs_id in self._abstracts :
            abstractList.append(self._conf.getAbstractMgr().getAbstractById(abs_id))

        generator = AbstractListToExcel(self._conf,abstractList, self._display)
        return send_file('AbstractList.csv', StringIO(generator.getExcelFile()), 'CSV')


#-------------------------------------------------------------------------------------

class RHConfModifDisplayCustomization( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModifDisplayCustomization

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )

    def _process( self ):
        p = conferences.WPConfModifDisplayCustomization(self, self._target)
        return p.display()

class RHConfModifDisplayMenu( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModifDisplayMenu

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._linkId = params.get("linkId", "")

    def _process( self ):
        p = conferences.WPConfModifDisplayMenu(self, self._target, self._linkId)
        return p.display()

class RHConfModifDisplayResources( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModifDisplayResources

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )

    def _process( self ):
        p = conferences.WPConfModifDisplayResources(self, self._target)
        return p.display()

class RHConfModifDisplayConfHeader( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModifDisplayConfHeader

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._optionalParams={}
        if params.has_key("modifiedText"):
            self._optionalParams["modifiedText"]=params.has_key("modifiedText")

    def _process( self ):
        p = conferences.WPConfModifDisplayConfHeader(self, self._target, optionalParams=self._optionalParams )
        return p.display()

class RHConfModifDisplayAddLink( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModifDisplayAddLink

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._linkId = params.get("linkId", "")
        self._cancel = params.get("cancel", "")
        self._submit = params.get("submit", "")
        self._params = params

    def _process( self ):
        if self._cancel:
            menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
            target = menu
            if self._linkId:
                target = menu.getLinkById(self._linkId)
            self._redirect(urlHandlers.UHConfModifDisplayMenu.getURL(target))
        elif self._submit:
            #create the link
            name = self._params.get("name", "[empty name]")
            if name.strip()=="":
                name="[empty name]"
            url = self._params.get("URL", "")
            displayTarget = self._params.get("displayTarget", "_blank")
            menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
            target = menu
            if self._linkId:
                target = menu.getLinkById(self._linkId)
            link = displayMgr.ExternLink(name, url)
            link.setCaption(name)
            link.setDisplayTarget(displayTarget)
            target.addLink(link)
            self._redirect(urlHandlers.UHConfModifDisplayMenu.getURL(link))
        else:
            p = conferences.WPConfModifDisplayAddLink(self, self._target, self._linkId )
            return p.display()


class RHConfModifDisplayAddPage( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModifDisplayAddLink

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._linkId = params.get("linkId", "")
        self._cancel = params.get("cancel", "")
        self._submit = params.get("submit", "")
        self._params = params

    def _process( self ):
        if self._cancel:
            menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
            target = menu
            if self._linkId:
                target = menu.getLinkById(self._linkId)
            self._redirect(urlHandlers.UHConfModifDisplayMenu.getURL(target))
        elif self._submit:
            #create the page
            intPagesMgr=internalPagesMgr.InternalPagesMgrRegistery().getInternalPagesMgr(self._conf)
            intPage=internalPagesMgr.InternalPage(self._conf)
            intPage.setTitle(self._params.get("title","[no title]"))
            intPage.setContent(self._params.get("content",""))
            intPagesMgr.addPage(intPage)
            #create the link
            name = self._params.get("name", "[empty name]")
            if name.strip()=="":
                name="[empty name]"
            content = self._params.get("content", "")
            displayTarget = self._params.get("displayTarget", "_blank")
            menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
            target = menu
            if self._linkId:
                target = menu.getLinkById(self._linkId)
            link = displayMgr.PageLink(name, intPage)
            link.setCaption(name)
            link.setDisplayTarget(displayTarget)
            target.addLink(link)
            self._redirect(urlHandlers.UHConfModifDisplayMenu.getURL(link))
        else:
            p = conferences.WPConfModifDisplayAddPage(self, self._target, self._linkId )
            return p.display()

class RHConfModifDisplayAddSpacer( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModifDisplayAddSpacer


    def _process( self ):
        menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
        spacer = displayMgr.Spacer()
        menu.addLink(spacer)
        self._redirect(urlHandlers.UHConfModifDisplayMenu.getURL(spacer))


class RHConfModifDisplayRemoveLink( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModifDisplayRemoveLink

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._linkId = params.get("linkId", "")
        self._cancel = params.get("cancel", "")
        self._confirm = params.get("confirm", "")


    def _process( self ):
        if self._cancel:
            menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
            link = menu.getLinkById(self._linkId)
            self._redirect(urlHandlers.UHConfModifDisplayMenu.getURL(link))
        elif self._confirm:
            menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
            link = menu.getLinkById(self._linkId)
            if isinstance(link, displayMgr.SystemLink):
                raise MaKaCError( _("You cannot remove a system link"))
            parent = link.getParent()
            if link.getType() == "page":
                page = link.getPage()
                internalPagesMgr.InternalPagesMgrRegistery().getInternalPagesMgr(self._conf).removePage(page)
            parent.removeLink(link)
            self._redirect(urlHandlers.UHConfModifDisplayMenu.getURL(self._target))
        else:
            menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
            link = menu.getLinkById(self._linkId)
            if link is None:
                raise NotFoundError( _("The link you are trying to delete no longer exists"))
            if isinstance(link, displayMgr.SystemLink):
                raise MaKaCError( _("You cannot remove a system link"))
            p = conferences.WPConfModifDisplayRemoveLink(self, self._target, link )
            return p.display()


class RHConfModifDisplayToggleLinkStatus( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModifDisplayToggleLinkStatus

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._linkId = params.get("linkId", "")


    def _process( self ):
        menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
        link=menu.getLinkById(self._linkId)
        if link.isEnabled():
            link.disable()
        else:
            link.enable()
        self._redirect(urlHandlers.UHConfModifDisplayMenu.getURL(link))


class RHConfModifDisplayToggleHomePage( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModifDisplayToggleHomePage

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._linkId = params.get("linkId", "")


    def _process( self ):
        menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
        link=menu.getLinkById(self._linkId)
        if link.getPage().isHome():
            link.getPage().setHome(False)
        else:
            for page in internalPagesMgr.InternalPagesMgrRegistery().getInternalPagesMgr(self._conf).getPagesList():
                page.setHome(False)
            link.getPage().setHome(True)
        self._redirect(urlHandlers.UHConfModifDisplayMenu.getURL(link))


class RHConfModifDisplayUpLink( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModifDisplayUpLink

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._linkId = params.get("linkId", "")


    def _process( self ):
        menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
        link = menu.getLinkById(self._linkId)
        parent = link.getParent()
        parent.upLink(link)
        self._redirect(urlHandlers.UHConfModifDisplayMenu.getURL(link))


class RHConfModifDisplayDownLink( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModifDisplayDownLink

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._linkId = params.get("linkId", "")


    def _process( self ):
        menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
        link = menu.getLinkById(self._linkId)
        parent = link.getParent()
        parent.downLink(link)
        self._redirect(urlHandlers.UHConfModifDisplayMenu.getURL(link))


class RHConfModifDisplayToggleTimetableView(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifDisplayToggleTimetableView

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self._linkId = params.get("linkId", "")

    def _process(self):
        menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
        link = menu.getLinkById(self._linkId)
        menu.set_timetable_detailed_view(not menu.is_timetable_detailed_view())
        self._redirect(urlHandlers.UHConfModifDisplayMenu.getURL(link))


class RHConfModifDisplayToggleTTDefaultLayout(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifDisplayToggleTTDefaultLayout

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self._linkId = params.get("linkId", "")

    def _process(self):
        menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
        link = menu.getLinkById(self._linkId)
        menu.toggle_timetable_layout()
        self._redirect(urlHandlers.UHConfModifDisplayMenu.getURL(link))


class RHConfModifDisplayModifyData(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifDisplayRemoveLink

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self._linkId = params.get("linkId", "")
        self._cancel = params.get("cancel", "")
        self._confirm = params.get("confirm", "")
        self._params = params

    def _process(self):

        if self._cancel:
            menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
            link = menu.getLinkById(self._linkId)
            self._redirect(urlHandlers.UHConfModifDisplayMenu.getURL(link))
        elif self._confirm:
            #create the link
            menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
            link = menu.getLinkById(self._linkId)
            if isinstance(link, displayMgr.SystemLink):
                raise MaKaCError( _("You cannot modify a system link"))
            name=self._params.get("name","[empty name]")
            if name.strip()=="":
                name="[empty name]"
            link.setCaption(name)
            if isinstance(link, displayMgr.ExternLink):
                link.setURL(self._params["url"])
            elif isinstance(link, displayMgr.PageLink):
                link.getPage().setContent(self._params.get("content",""))
            link.setDisplayTarget(self._params.get("displayTarget", "_blank"))
            self._redirect(urlHandlers.UHConfModifDisplayMenu.getURL(link))
        else:
            menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
            link = menu.getLinkById(self._linkId)
            if isinstance(link, displayMgr.SystemLink):
                raise MaKaCError( _("You cannot modify a system link"))
            if isinstance(link, displayMgr.ExternLink):
                p = conferences.WPConfModifDisplayModifyData(self, self._target, link )
            else:
                p = conferences.WPConfModifDisplayModifyPage(self, self._target, link )
            return p.display()

class RHConfModifDisplayModifySystemData( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModifDisplayRemoveLink

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._linkId = params.get("linkId", "")
        self._cancel = params.get("cancel", "")
        self._confirm = params.get("confirm", "")
        self._params = params

    def _process( self ):

        if self._cancel:
            menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
            link = menu.getLinkById(self._linkId)
        elif self._confirm:
            #create the link
            menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
            link = menu.getLinkById(self._linkId)
            if isinstance(link, displayMgr.SystemLink):
                name=self._params.get("name","[empty name]")
                if name.strip()=="":
                    name="[empty name]"
                link.setCaption(name)
        else:
            menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
            link = menu.getLinkById(self._linkId)
            if isinstance(link, displayMgr.SystemLink):
                p = conferences.WPConfModifDisplayModifySystemData(self, self._target, link )
                return p.display()
        self._redirect(urlHandlers.UHConfModifDisplayMenu.getURL(link))

class RHConfModifFormatTitleColorBase( RHConferenceModifBase ):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._linkId = params.get("linkId", "")
        self._formatOption = params.get("formatOption", "")
        self._colorCode = params.get("colorCode", "")
        self._apply =  params.has_key( "apply" )
        self._remove =  params.has_key( "remove" )

    def _process( self ):
        format = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getFormat()
        if self._formatOption:
            if self._apply:
                format.setColorCode(self._formatOption, "#" + self._colorCode)
            elif self._remove:
                format.clearColorCode(self._formatOption)
        redirecturl = urlHandlers.UHConfModifDisplayCustomization.getURL(self._conf)
        redirecturl.addParam("formatOption", self._formatOption)
        self._redirect("%s#colors"%redirecturl)

class RHConfModifFormatTitleBgColor( RHConfModifFormatTitleColorBase ):
    _uh = urlHandlers.UHConfModifFormatTitleBgColor

class RHConfModifFormatTitleTextColor( RHConfModifFormatTitleColorBase ):
    _uh = urlHandlers.UHConfModifFormatTitleBgColor

class RHConfSaveLogo( RHConferenceModifBase ):

    def _getNewTempFile( self ):
        cfg = Config.getInstance()
        tempPath = cfg.getUploadedFilesTempDir()
        tempFileName = tempfile.mkstemp( suffix="IndicoLogo.tmp", dir = tempPath )[1]
        return tempFileName

    def _saveFileToTemp(self, fs):
        fileName = self._getNewTempFile()
        fs.save(fileName)
        return fileName

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        if not hasattr(self,"_filePath"):
            self._filePath = self._saveFileToTemp(params["file"])
            self._tempFilesToDelete.append(self._filePath)
        self._fileName = params["file"].filename


    def _process( self ):
        f = conference.LocalFile()
        f.setName( "Logo" )
        f.setDescription( "This is the logo for the conference" )
        f.setFileName( self._fileName )
        f.setFilePath( self._filePath )
        self._conf.setLogo( f )
        self._redirect( "%s#logo"%urlHandlers.UHConfModifDisplayCustomization.getURL( self._conf ) )


class RHConfRemoveLogo( RHConferenceModifBase ):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )

    def _process( self ):
        self._conf.removeLogo()
        self._redirect( "%s#logo"%urlHandlers.UHConfModifDisplayCustomization.getURL( self._conf ) )

class RHConfSaveCSS( RHConferenceModifBase ):

    def _getNewTempFile( self ):
        cfg = Config.getInstance()
        tempPath = cfg.getUploadedFilesTempDir()
        tempFileName = tempfile.mkstemp( suffix="IndicoCSS.tmp", dir = tempPath )[1]
        return tempFileName

    def _saveFileToTemp(self, fs):
        fileName = self._getNewTempFile()
        fs.save(fileName)
        return fileName

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._params = params
        if self._params.has_key("FP"):
            self._filePath = self._params["FP"]
            self._fileName = "TemplateInUse"
        else:
            if not hasattr(self,"_filePath"):
                self._filePath = self._saveFileToTemp(params["file"])
                self._tempFilesToDelete.append(self._filePath)
            self._fileName = params["file"].filename
        if self._fileName.strip() == "":
            raise FormValuesError(_("Please, choose the file to upload first"))

    def _process( self ):
        f = conference.LocalFile()
        f.setName( "CSS" )
        f.setDescription( "This is the css for the conference" )
        f.setFileName( self._fileName )
        f.setFilePath( self._filePath )
        sm = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getStyleManager()
        sm.setCSS( f )
        self._redirect( "%s#css"%urlHandlers.UHConfModifDisplayCustomization.getURL( self._conf ) )


class RHConfRemoveCSS( RHConferenceModifBase ):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )

    def _process( self ):
        sm = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getStyleManager()
        sm.removeCSS()
        # Since this function makes sure no template is used make sure that
        # one of the standard ones is not used
        sm.useLocalCSS()
        self._redirect( "%s#css"%urlHandlers.UHConfModifDisplayCustomization.getURL( self._conf ) )

class RHConfModifPreviewCSS(RoomBookingDBMixin, RHConferenceModifBase):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._params = params

    def _process( self ):
        # Call a webpage that will handle the task
        CSS_Temp_Id = self._params.get("cssId", "")
        p = conferences.WPConfModifPreviewCSS(self, self._conf, CSS_Temp_Id)
        return p.display()


class RHConfUseCSS( RHConferenceModifBase ):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._params = params
        self._selectedTpl = self._params.get("selectedTpl")

    def _process( self ):
        styleMgr = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getStyleManager()
        if self._selectedTpl == "css":
            styleMgr.useLocalCSS()
        elif self._selectedTpl:
            styleMgr.setCSS(self._selectedTpl)
        self._redirect( "%s#css"%urlHandlers.UHConfModifDisplayCustomization.getURL( self._conf ) )

class RHConfSavePic( RHConferenceModifBase ):

    def __init__(self, req):
        RHConferenceModifBase.__init__(self, req)
        self._tempFiles = {}

    def _getNewTempFile( self ):
        cfg = Config.getInstance()
        tempPath = cfg.getUploadedFilesTempDir()
        tempFileName = tempfile.mkstemp( suffix="IndicoPic.tmp", dir = tempPath )[1]
        return tempFileName

    def _saveFileToTemp(self, fs):
        if fs not in self._tempFiles:
            fileName = self._getNewTempFile()
            fs.save(fileName)
            self._tempFiles[fs] = fileName
        return self._tempFiles[fs]

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._filePath = self._saveFileToTemp(params["file"])
        self._tempFilesToDelete.append(self._filePath)
        self._fileName = params["file"].filename
        self._params = params


    def _process( self ):
        if self._fileName == "":
            return json.dumps({'status': "ERROR", 'info': {'message':_("No file has been attached")}})
        f = conference.LocalFile()
        f.setFileName( self._fileName )
        f.setFilePath( self._filePath )
        im = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getImagesManager()
        pic = im.addPic( f )
        info={"name": f.getFileName(),
                "id": f.getId(),
                "picURL": str(urlHandlers.UHConferencePic.getURL(pic))}
        return json.dumps({'status': "OK", 'info': info}, textarea=True)

class RHConfModifTickerTapeAction( RHConferenceModifBase ):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        dm = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf)
        self._tickerTape=dm.getTickerTape()
        self._status=params.has_key("ttStatus")
        self._saveText=params.has_key("savettText")
        self._text=params.get("ttText","")
        self._simpleTextEnabled=params.has_key("simpleText")
        self._nowHappeningEnabled=params.has_key("nowHappening")

    def _process( self ):
        url=urlHandlers.UHConfModifDisplayConfHeader.getURL( self._conf )
        if self._status:
            self._tickerTape.setActive(not self._tickerTape.isActive())
        if self._saveText:
            self._tickerTape.setText(self._text)
            url.addParam("modifiedText", "True")
        if self._nowHappeningEnabled:
            self._tickerTape.setNowHappeningEnabled(not self._tickerTape.isNowHappeningEnabled())
        if self._simpleTextEnabled:
            self._tickerTape.setSimpleTextEnabled(not self._tickerTape.isSimpleTextEnabled())
        self._redirect( "%s#tickertape"%url )

class RHConfModifToggleSearch( RHConferenceModifBase ):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._displayMgr = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf)
        self._searchEnabled=self._displayMgr.getSearchEnabled()

    def _process( self ):
        url=urlHandlers.UHConfModifDisplayConfHeader.getURL( self._conf )
        self._displayMgr.setSearchEnabled(not self._searchEnabled)
        self._redirect( "%s#headerFeatures"%url )


class RHConfModifToggleNavigationBar( RHConferenceModifBase ):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._displayMgr = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf)
        self._navigationBarEnabled=self._displayMgr.getDisplayNavigationBar()

    def _process( self ):
        url=urlHandlers.UHConfModifDisplayConfHeader.getURL( self._conf )
        self._displayMgr.setDisplayNavigationBar(not self._navigationBarEnabled)
        self._redirect( "%s#headerFeatures"%url )

class RHConfAddContribType(RHConferenceModifBase):
    _uh = urlHandlers.UHConfAddContribType

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self._typeName = params.get("ctName", "")
        self._typeDescription = params.get("ctDescription", "")
        self._typeId = params.get("typeId", "")
        self._cancel = params.get("cancel", "")
        self._save = params.get("save", "")

    def _process( self ):
        if self._cancel:
            self._redirect(urlHandlers.UHConferenceModification.getURL(self._conf))
        elif self._save:
            ct = self._conf.newContribType(self._typeName, self._typeDescription)

            # Filtering criteria: by default make new contribution type checked
            filters = session.setdefault('ContributionFilterConf%s' % self._conf.getId(), {})
            if 'types' in filters:
                #Append the new type to the existing list
                newDict = filters['types'][:]
                newDict.append(ct.getId())
                filters['types'] = newDict[:]
            else:
                #Create a new entry for the dictionary containing the new type
                filters['types'] = [ct.getId()]
            session.modified = True

            self._redirect(urlHandlers.UHConferenceModification.getURL(self._conf))
        else:
            p = conferences.WPConfAddContribType(self, self._target )
            return p.display()


class RHConfRemoveContribType(RHConferenceModifBase):
    _uh = urlHandlers.UHConfRemoveContribType

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        selTypeId = self._normaliseListParam( params.get( "types", [] ) )
        self._contribTypes = []
        for id in selTypeId:
            self._contribTypes.append(self._conf.getContribTypeById(id))


    def _process(self):
        for ct in self._contribTypes:
            self._conf.removeContribType(ct)
        self._redirect(urlHandlers.UHConferenceModification.getURL(self._conf))


class RHConfContribTypeBase(RHConferenceModifBase):

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        l = locators.WebLocator()
        l.setContribType( params )
        self._contribType = self._target = l.getObject()


class RHConfEditContribType(RHConfContribTypeBase):

    def _checkParams(self, params):
        RHConfContribTypeBase._checkParams(self, params)
        self._save = params.get("save", "")
        self._name = params.get("ctName", "")
        self._cancel = params.get("cancel", "")
        self._description = params.get("ctDescription", "")

    def _process(self):
        if self._cancel:
            self._redirect(urlHandlers.UHConferenceModification.getURL(self._conf))
        elif self._save:
            self._target.setName(self._name)
            self._target.setDescription(self._description)
            self._redirect(urlHandlers.UHConferenceModification.getURL(self._conf))
        else:
            p = conferences.WPConfEditContribType(self, self._target )
            return p.display()


class ContribFilterCrit(filters.FilterCriteria):
    _availableFields = { \
        contribFilters.TypeFilterField.getId():contribFilters.TypeFilterField, \
        contribFilters.StatusFilterField.getId():contribFilters.StatusFilterField, \
        contribFilters.TrackFilterField.getId():contribFilters.TrackFilterField, \
        contribFilters.MaterialFilterField.getId():contribFilters.MaterialFilterField, \
        contribFilters.SessionFilterField.getId():contribFilters.SessionFilterField }


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

class RHContributionListBase(RHConferenceModifBase):

    def _checkProtection(self):
        from MaKaC.webinterface.rh.reviewingModif import RCPaperReviewManager
        if not RCPaperReviewManager.hasRights(self):
            RHConferenceModifBase._checkProtection(self)


class RHContributionList( RoomBookingDBMixin, RHContributionListBase ):
    _uh = urlHandlers.UHConfModifContribList

    def _checkProtection(self):
        from MaKaC.webinterface.rh.reviewingModif import RCPaperReviewManager
        if not RCPaperReviewManager.hasRights(self):
            RHContributionListBase._checkProtection(self)

    def _resetFilters( self, sessionData ):
        """
        Brings the filter data to a consistent state (websession),
        marking everything as "checked"
        """

        sessionData.clear()
        sessionData["type"] = map(lambda ctype: ctype.getId(), self._conf.getContribTypeList())
        sessionData["track"] = map(lambda track: track.getId(), self._conf.getTrackList())
        sessionData["session"] = map(lambda ses: ses.getId(), self._conf.getSessionList())
        sessionData["status"] = map(lambda status: ContribStatusList.getId(status), ContribStatusList.getList())
        lmaterial = []
        paperId = materialFactories.PaperFactory().getId()
        slidesId = materialFactories.SlidesFactory().getId()
        for matId in ["--other--","--none--",paperId,slidesId]: # wtf? doesn't that simply re-create the list?
            lmaterial.append(matId)
        sessionData["material"] = lmaterial
        sessionData["typeShowNoValue"] = True
        sessionData["trackShowNoValue"] = True
        sessionData["sessionShowNoValue"] = True

        return sessionData

    def _updateFilters( self, sessionData, params ):
        """
        Updates the filter parameters in the websession with those
        coming from the HTTP request
        """

        sessionData["status"] = []
        sessionData["material"] = []
        sessionData.update(params)
        sessionData["type"] = utils.normalizeToList(params.get('types', []))
        sessionData["track"] = utils.normalizeToList(params.get('tracks', []))
        sessionData['session'] = utils.normalizeToList(params.get('sessions', []))

        # update these elements in the session so that the parameters that are
        # passed are always taken into account (sessionData.update is not
        # enough, since the elements that are ommitted in params would just be
        # ignored

        sessionData['typeShowNoValue'] = params.has_key('typeShowNoValue')
        sessionData['trackShowNoValue'] = params.has_key('trackShowNoValue')
        sessionData['sessionShowNoValue'] = params.has_key('sessionShowNoValue')

        return sessionData

    def _buildFilteringCriteria(self, sessionData):
        """
        Creates the Filtering Criteria object, without changing the existing
        session data (sessionData is cloned, not directly changed)
        """
        sessionCopy = sessionData.copy()

        # Build the filtering criteria
        filterCrit = ContribFilterCrit(self._conf, sessionCopy)

        filterCrit.getField("type").setShowNoValue(sessionCopy.get('typeShowNoValue'))
        filterCrit.getField("track").setShowNoValue(sessionCopy.get('trackShowNoValue'))
        filterCrit.getField("session").setShowNoValue(sessionCopy.get('sessionShowNoValue'))

        return filterCrit

    def _checkAction(self, params, filtersActive, sessionData, operation, isBookmark):
        """
        Decides what to do with the request parameters, depending
        on the type of operation that is requested
        """

        # user chose to reset the filters
        if operation ==  'resetFilters':
            self._filterUsed = False
            sessionData = self._resetFilters(sessionData)

        # user set the filters
        elif operation ==  'setFilters':
            self._filterUsed = True
            sessionData = self._updateFilters(sessionData, params)

        # user has changed the display options
        elif operation == 'setDisplay':
            self._filterUsed = filtersActive

        # session is empty (first time)
        elif not filtersActive:
            self._filterUsed = False
            sessionData = self._resetFilters(sessionData)
        else:
            self._filterUsed = True

        # if this is accessed through a direct link, the session is empty, so set default values
        if isBookmark:
            sessionData = self._resetFilters(sessionData)
            if operation != 'resetFilters':
                sessionData = self._updateFilters(sessionData, params)

        # preserve the order and sortBy parameters, whatever happens
        sessionData['order'] = params.get('order', 'down')
        sessionData['sortBy'] = params.get('sortBy', 'number')

        return sessionData

    def _checkParams( self, params ):
        RHContributionListBase._checkParams( self, params )
        operationType = params.get('operationType')
        sessionData = session.get('ContributionFilterConf%s' % self._conf.getId())

        # check if there is information already
        # set in the session variables
        if sessionData:
            # work on a copy
            sessionData = sessionData.copy()
            filtersActive =  sessionData.get('filtersActive', False)
        else:
            # set a default, empty dict
            sessionData = {}
            filtersActive = False

        if params.has_key("resetFilters"):
            operation =  'resetFilters'
        elif operationType ==  'filter':
            operation =  'setFilters'
        elif operationType ==  'display':
            operation =  'setDisplay'
        else:
            operation = None

        isBookmark = params.has_key("isBookmark")
        sessionData = self._checkAction(params, filtersActive, sessionData, operation, isBookmark)
        # Maintain the state about filter usage
        sessionData['filtersActive'] = self._filterUsed;
        # Save the web session
        session['ContributionFilterConf%s' % self._conf.getId()] = sessionData
        self._filterCrit = self._buildFilteringCriteria(sessionData)
        self._sortingCrit = ContribSortingCrit([sessionData.get("sortBy", "number").strip()])
        self._order = sessionData.get("order", "down")
        self._authSearch = sessionData.get("authSearch", "")

    def _process( self ):
        p = conferences.WPModifContribList(self, self._target, self._filterUsed)
        return p.display(authSearch=self._authSearch,\
                        filterCrit=self._filterCrit, sortingCrit=self._sortingCrit, order=self._order)


class RHContribQuickAccess(RHConferenceModifBase):

    def _checkParams(self,params):
        RHConferenceModifBase._checkParams(self,params)
        self._contrib=self._target.getContributionById(params.get("selContrib",""))

    def _process(self):
        url=urlHandlers.UHConfModifContribList.getURL(self._target)
        if self._contrib is not None:
            url=urlHandlers.UHContributionModification.getURL(self._contrib)
        self._redirect(url)

#-------------------------------------------------------------------------------------

class RHAbstractsParticipantList(RHConfModifCFABase):

    def _checkProtection( self ):
        if len( self._conf.getCoordinatedTracks( self._getUser() ) ) == 0:
            RHConferenceModifBase._checkProtection( self )

    def _checkParams( self, params ):
        RHConfModifCFABase._checkParams( self, params )
        self._abstractIds = normaliseListParam( params.get("abstracts", []) )
        self._displayedGroups = params.get("displayedGroups", [])
        if type(self._displayedGroups) != list:
            self._displayedGroups = [self._displayedGroups]
        self._clickedGroup = params.get("clickedGroup","")

    def _setGroupsToDisplay(self):
        if self._clickedGroup in self._displayedGroups:
            self._displayedGroups.remove(self._clickedGroup)
        else:
            self._displayedGroups.append(self._clickedGroup)

    def _process( self ):
        #This is a plain text exception but an exception should be raised here !
        if not self._abstractIds:
            return  _("There is no abstract.")

        submitters = OOBTree()
        primaryAuthors = OOBTree()
        coAuthors = OOBTree()
        submitterEmails = set()
        primaryAuthorEmails = set()
        coAuthorEmails = set()

        self._setGroupsToDisplay()

        abMgr = self._conf.getAbstractMgr()
        for abstId in self._abstractIds:
            abst = abMgr.getAbstractById(abstId)
            #Submitters

            subm = abst.getSubmitter()
            if subm.getSurName().lower().strip() != "" or subm.getFirstName().lower().strip() != "" or subm.getEmail().lower().strip() != "":
                keySB = "%s-%s-%s"%(subm.getSurName().lower(), subm.getFirstName().lower(), subm.getEmail().lower())
                submitters[keySB] = subm
                submitterEmails.add(subm.getEmail())
            #Primary authors
            for pAut in abst.getPrimaryAuthorList():
                if pAut.getSurName().lower().strip() == "" and pAut.getFirstName().lower().strip() == "" and pAut.getEmail().lower().strip() == "":
                    continue
                keyPA = "%s-%s-%s"%(pAut.getSurName().lower(), pAut.getFirstName().lower(), pAut.getEmail().lower())
                primaryAuthors[keyPA] = pAut
                primaryAuthorEmails.add(pAut.getEmail())
            #Co-authors
            for coAut in abst.getCoAuthorList():
                if coAut.getSurName().lower().strip() == "" and coAut.getFirstName().lower().strip() == "" and coAut.getEmail().lower().strip() == "":
                    continue
                keyCA = "%s-%s-%s"%(coAut.getSurName().lower(), coAut.getFirstName().lower(), coAut.getEmail().lower())
                coAuthors[keyCA] = coAut
                coAuthorEmails.add(coAut.getEmail())
        emailList = {"submitters":{},"primaryAuthors":{},"coAuthors":{}}
        emailList["submitters"]["tree"] = submitters
        emailList["primaryAuthors"]["tree"] = primaryAuthors
        emailList["coAuthors"]["tree"] = coAuthors
        emailList["submitters"]["emails"] = submitterEmails
        emailList["primaryAuthors"]["emails"] = primaryAuthorEmails
        emailList["coAuthors"]["emails"] = coAuthorEmails
        p = conferences.WPConfParticipantList(self, self._target, emailList, self._displayedGroups, self._abstractIds )
        return p.display()


class RHNewAbstract(RHConfModifCFABase, AbstractParam):

    def __init__(self, req):
        RHConfModifCFABase.__init__(self, req)
        AbstractParam.__init__(self)

    def _checkParams(self, params):
        RHConfModifCFABase._checkParams(self, params)
        #if the user is not logged in we return immediately as this form needs
        #   the user to be logged in and therefore all the checking below is not
        #   necessary
        if self._getUser() is None:
            return
        AbstractParam._checkParams(self, params, self._conf, request.content_length)

    def _doValidate(self):
        #First, one must validate that the information is fine
        errors = self._abstractData.check()
        if errors:
            p = conferences.WPModNewAbstract(
                self, self._target, self._abstractData)
            pars = self._abstractData.toDict()
            pars["action"] = self._action
            return p.display(**pars)
        #Then, we create the abstract object and set its data to the one
        #   received
        cfaMgr = self._target.getAbstractMgr()
        abstract = cfaMgr.newAbstract(self._getUser())
        #self._setAbstractData(abstract)
        self._abstractData.setAbstractData(abstract)
        #Finally, we display the abstract list page
        self._redirect(urlHandlers.UHConfAbstractList.getURL(self._conf))

    def _process(self):
        if self._action == "CANCEL":
            self._redirect(
                urlHandlers.UHConfAbstractManagment.getURL(self._target))
        elif self._action == "VALIDATE":
            return self._doValidate()
        else:
            p = conferences.WPModNewAbstract(
                self, self._target, self._abstractData)
            pars = self._abstractData.toDict()
            return p.display(**pars)



class RHContribsActions:
    """
    class to select the action to do with the selected abstracts
    """
    def __init__(self, req):
        assert req is None

    def process(self, params):
        if params.has_key("PDF"):
            return RHContribsToPDF(None).process(params)
        elif params.has_key("excel.x"):
            return  RHContribsToExcel(None).process(params)
        elif params.has_key("xml.x"):
            return  RHContribsToXML(None).process(params)
        elif params.has_key("AUTH"):
            return RHContribsParticipantList(None).process(params)
        elif params.has_key("move"):
            return RHMoveContribsToSession(None).process(params)
        elif params.has_key("PKG"):
            return RHMaterialPackage(None).process(params)
        elif params.has_key("PROC"):
            return RHProceedings(None).process(params)
        return "no action to do"


class RHContribsToPDFMenu(RHConferenceModifBase):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._contribIds = self._normaliseListParam( params.get("contributions", []) )
        self._contribs = []
        for id in self._contribIds:
            self._contribs.append(self._conf.getContributionById(id))
        self._displayType = params.get("displaytype", None)

    def _process( self ):
        from MaKaC.PDFinterface.conference import ContributionBook
        if not self._displayType:
            wp =  conferences.WPConfModifContribToPDFMenu(self, self._conf, self._contribIds)
            return wp.display()

        elif self._displayType == "bookOfAbstract":
            tz = self._target.getTimezone()
            filename = "{0} - Book of abstracts.pdf".format(self._target.getTitle())

            pdf = ContributionBook(self._target, self.getAW(), self._contribs, tz=tz)
            return send_file(filename, pdf.generate(), 'PDF')

        elif self._displayType == "bookOfAbstractBoardNo":
            tz = self._target.getTimezone()
            filename = "{0} - Book of abstracts.pdf".format(self._target.getTitle())
            pdf = ContributionBook(self._target, self.getAW(), self._contribs, tz=tz, sort_by="boardNo")
            return send_file(filename, pdf.generate(), 'PDF')

        elif self._displayType == "ContributionList":
            tz = self._conf.getTimezone()
            filename = "{0} - Contributions.pdf".format(self._target.getTitle())
            if not self._contribs:
                return "No contributions to print"

            contrib_pdf = ContribsToPDF(self._conf, self._contribs)
            fpath = contrib_pdf.generate()

            return send_file(filename, fpath, 'PDF')


class RHContribsToPDF(RHConferenceModifBase):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._contribIds = self._normaliseListParam( params.get("contributions", []) )
        self._contribs = []
        for id in self._contribIds:
            self._contribs.append(self._conf.getContributionById(id))

    def _process( self ):
        tz = self._conf.getTimezone()
        filename = "Contributions.pdf"
        if not self._contribs:
            return "No contributions to print"
        pdf = ContribsToPDF(self._conf, self._contribs)
        return send_file(filename, pdf.generate(), 'PDF')


class RHContribsToExcel(RHConferenceModifBase):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._contribIds = self._normaliseListParam( params.get("contributions", []) )
        self._contribs = []
        for id in self._contribIds:
            self._contribs.append(self._conf.getContributionById(id))

    def _process( self ):
        tz = self._conf.getTimezone()
        filename = "Contributions.csv"
        if not self._contribs:
            return "No contributions to print"
        excel = ContributionsListToExcel(self._conf, self._contribs, tz=tz)
        return send_file(filename, StringIO(excel.getExcelFile()), 'CSV')


class RHContribsToXML(RHConferenceModifBase):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._contribIds = self._normaliseListParam( params.get("contributions", []) )
        self._contribs = []
        for id in self._contribIds:
            self._contribs.append(self._conf.getContributionById(id))
    def _process( self ):
        filename = "Contributions.xml"
        from MaKaC.common.fossilize import fossilize
        resultFossil = fossilize(self._contribs)
        serializer = Serializer.create('xml')
        return send_file(filename, StringIO(serializer(resultFossil)), 'XML')


class RHContribsParticipantList(RHConferenceModifBase):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._contribIds = normaliseListParam( params.get("contributions", []) )
        self._displayedGroups = self._normaliseListParam( params.get("displayedGroups", []) )
        self._clickedGroup = params.get("clickedGroup","")

    def _setGroupsToDisplay(self):
        if self._clickedGroup in self._displayedGroups:
            self._displayedGroups.remove(self._clickedGroup)
        else:
            self._displayedGroups.append(self._clickedGroup)

    def _process( self ):
        if not self._contribIds:
            return  i18nformat("""<table align=\"center\" width=\"100%%\"><tr><td> _("There are no contributions") </td></tr></table>""")

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
                primaryAuthors[keyPA] = pAut
                if pAut.getEmail() != "":
                    primaryAuthorEmails.add(pAut.getEmail())
            #Co-authors
            for coAut in contrib.getCoAuthorList():
                if coAut.getFamilyName().lower().strip() == "" and coAut.getFirstName().lower().strip() == "" and coAut.getEmail().lower().strip() == "":
                    continue
                keyCA = "%s-%s-%s"%(coAut.getFamilyName().lower(), coAut.getFirstName().lower(), coAut.getEmail().lower())
                coAuthors[keyCA] = coAut
                if coAut.getEmail() != "":
                    coAuthorEmails.add(coAut.getEmail())
            #Presenters
            for pres in contrib.getSpeakerList():
                if pres.getFamilyName().lower().strip() == "" and pres.getFirstName().lower().strip() == "" and pres.getEmail().lower().strip() == "":
                    continue
                keyP = "%s-%s-%s"%(pres.getFamilyName().lower(), pres.getFirstName().lower(), pres.getEmail().lower())
                speakers[keyP] = pres
                if pres.getEmail() != "":
                    speakerEmails.add(pres.getEmail())
        emailList = {"speakers":{},"primaryAuthors":{},"coAuthors":{}}
        emailList["speakers"]["tree"] = speakers
        emailList["primaryAuthors"]["tree"] = primaryAuthors
        emailList["coAuthors"]["tree"] = coAuthors
        emailList["speakers"]["emails"] = speakerEmails
        emailList["primaryAuthors"]["emails"] = primaryAuthorEmails
        emailList["coAuthors"]["emails"] = coAuthorEmails
        p = conferences.WPConfModifParticipantList(self, self._target, emailList, self._displayedGroups, self._contribIds )
        return p.display()


class RHMoveContribsToSession(RHConferenceModifBase):

    def _checkParams(self,params):
        RHConferenceModifBase._checkParams(self,params)
        self._action=""
        self._session=self._target.getSessionById(params.get("targetSession",""))
        self._contribIds=self._normaliseListParam(params.get("contributions",[]))
        if params.has_key("OK"):
            if self._session is not None and self._session.isClosed():
                raise NoReportError(_("""The modification of the session "%s" is not allowed because it is closed""")%self._session.getTitle())
            self._contribIds=self._normaliseListParam(params.get("contributions","").split(","))
            self._action="MOVE"
        elif params.has_key("CANCEL"):
            self._action="CANCEL"
        elif params.has_key("CONFIRM"):
            self._action="MOVE_CONFIRMED"
        elif params.has_key("CONFIRM_ALL"):
            self._action="MOVE_ALL_CONFIRMED"

    def _needsWarning(self,contrib):
        return (contrib.getSession() is not None and \
                            contrib.getSession()!=self._session) or \
                            (contrib.getSession() is None and \
                            self._session is not None and \
                            contrib.isScheduled())

    def _process( self ):
        url=urlHandlers.UHConfModifContribList.getURL(self._target)
        if self._action=="CANCEL":
            self._redirect(url)
            return
        elif self._action in ("MOVE","MOVE_CONFIRMED","MOVE_ALL_CONFIRMED"):
            contribList=[]
            for id in self._contribIds:
                contrib=self._target.getContributionById(id)
                if contrib is None:
                    continue
                if self._needsWarning(contrib):
                    if self._action=="MOVE":
                        p=conferences.WPModMoveContribsToSessionConfirmation(self,self._target)
                        return p.display(contribIds=self._contribIds,targetSession=self._session)
                    elif self._action=="MOVE_CONFIRMED":
                        continue
                if contrib.getSession() is not None and contrib.getSession().isClosed():
                    raise NoReportError(_("""The contribution "%s" cannot be moved because it is inside of the session "%s" that is closed""")%(contrib.getId(), contrib.getSession().getTitle()))
                contribList.append(contrib)
            for contrib in contribList:
                contrib.setSession(self._session)
            self._redirect(url)
            return
        p=conferences.WPModMoveContribsToSession(self,self._target)
        return p.display(contribIds=self._contribIds)

class RHMaterialPackageAbstract(RHConferenceModifBase):
    # Export a Zip file

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        abstractIds = self._normaliseListParam( params.get("abstracts", []) )
        self._abstracts = []
        for aID in abstractIds:
            self._abstracts.append(self._conf.getAbstractMgr().getAbstractById(aID))

    def _process( self ):
        if not self._abstracts:
            return FormValuesError(_("No abstract selected"))
        p = AbstractPacker(self._conf)
        path = p.pack(self._abstracts, ZIPFileHandler())
        return send_file('abstractFiles.zip', path, 'ZIP', inline=False)


class RHMaterialPackage(RHConferenceModifBase):

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self._contribIds = self._normaliseListParam(params.get("contributions", []))
        self._contribs = []
        for id in self._contribIds:
            self._contribs.append(self._conf.getContributionById(id))

    def _process(self):
        if not self._contribs:
            return "No contribution selected"
        p=ContribPacker(self._conf)
        path=p.pack(self._contribs, ZIPFileHandler())
        if not p.getItems():
            raise NoReportError(_("The selected package does not contain any items"))
        return send_file('material.zip', path, 'ZIP', inline=False)


class RHProceedings(RHConferenceModifBase):

    def _process( self ):
        p=ProceedingsPacker(self._conf)
        path=p.pack(ZIPFileHandler())
        return send_file('proceedings.zip', path, 'ZIP', inline=False)


class RHAbstractBook( RHConfModifCFABase ):
    _uh = urlHandlers.UHConfModAbstractBook

    def _checkParams( self, params ):
        RHConfModifCFABase._checkParams( self, params )

    def _process( self ):
        p = conferences.WPModAbstractBook(self,self._target)
        return p.display()


class RHAbstractBookToogleShowIds( RHConfModifCFABase ):
    _uh = urlHandlers.UHConfModAbstractBookToogleShowIds

    def _process( self ):
        self._conf.getBOAConfig().setShowIds(not self._conf.getBOAConfig().getShowIds())
        self._redirect( urlHandlers.UHConfModAbstractBook.getURL( self._conf ) )

class RHFullMaterialPackage(RHConferenceModifBase):
    _uh=urlHandlers.UHConfModFullMaterialPackage

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )

    def _process( self ):
        p = conferences.WPFullMaterialPackage(self,self._target)
        return p.display()


class RHFullMaterialPackagePerform(RHConferenceModifBase):
    _uh=urlHandlers.UHConfModFullMaterialPackagePerform

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._days=self._normaliseListParam(params.get("days",[]))
        self._mainResource = (params.get("mainResource","") != "")
        self._fromDate = ""
        fromDay = params.get("fromDay","")
        fromMonth = params.get("fromMonth","")
        fromYear = params.get("fromYear","")
        if fromDay != "" and fromMonth != "" and fromYear != "" and \
           fromDay != "dd" and fromMonth != "mm" and fromYear != "yyyy":
            self._fromDate = "%s %s %s"%(fromDay, fromMonth, fromYear)
        self._cancel = params.has_key("cancel")
        self._materialTypes=self._normaliseListParam(params.get("materialType",[]))
        self._sessionList = self._normaliseListParam(params.get("sessionList",[]))

    def _process( self ):
        if not self._cancel:
            if self._materialTypes:
                p=ConferencePacker(self._conf, self._aw)
                path=p.pack(self._materialTypes, self._days, self._mainResource, self._fromDate, ZIPFileHandler(),self._sessionList)
                if not p.getItems():
                    raise NoReportError(_("The selected package does not contain any items."))
                return send_file('full-material.zip', path, 'ZIP', inline=False)
            raise NoReportError(_("You have to select at least one material type"))
        else:
            self._redirect( urlHandlers.UHConfModifTools.getURL( self._conf ) )

class RHModifSessionCoordRights( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfPerformDataModif

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._rightId = params.get("rightId", "")

    def _process( self ):
        if self._rightId != "":
            if self._conf.hasSessionCoordinatorRight(self._rightId):
                self._conf.removeSessionCoordinatorRight(self._rightId)
            else:
                self._conf.addSessionCoordinatorRight(self._rightId)
            self._redirect( "%s#sessionCoordinatorRights"%urlHandlers.UHConfModifAC.getURL( self._conf) )


class RHConfModifPendingQueues( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModifPendingQueues

    def _process( self ):
        p = conferences.WPConfModifPendingQueues( self, self._target, self._getRequestParams().get("tab","conf_submitters") )
        return p.display()

class RHConfModifPendingQueuesActionConfMgr:
    """
    class to select the action to do with the selected pending conference submitters
    """

    _uh = urlHandlers.UHConfModifPendingQueuesActionConfMgr

    def __init__(self, req):
        assert req is None

    def process(self, params):
        if 'remove' in params:
            return RHConfModifPendingQueuesRemoveConfMgr(None).process(params)
        elif 'reminder' in params:
            return RHConfModifPendingQueuesReminderConfMgr(None).process(params)
        return "no action to do"

class RHConfModifPendingQueuesRemoveConfMgr( RHConferenceModifBase ):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._pendingConfMgrIds = self._normaliseListParam( params.get("pendingUsers", []) )
        self._pendingConfMgrs = []
        for id in self._pendingConfMgrIds:
            self._pendingConfMgrs.extend(self._conf.getPendingQueuesMgr().getPendingConfManagersByEmail(id))
        self._remove=params.has_key("confirm")
        self._confirmed=params.has_key("confirm") or params.has_key("cancel")

    def _process( self ):
        url=urlHandlers.UHConfModifPendingQueues.getURL(self._conf)
        url.addParam("tab","conf_managers")
        if self._pendingConfMgrs == []:
            self._redirect(url)
        if self._confirmed:
            if self._remove:
                for ps in self._pendingConfMgrs:
                    self._conf.getPendingQueuesMgr().removePendingConfManager(ps)
            self._redirect(url)
        else:
            wp = conferences.WPConfModifPendingQueuesRemoveConfMgrConfirm(self, self._conf, self._pendingConfMgrIds)
            return wp.display()

class RHConfModifPendingQueuesReminderConfMgr( RHConferenceModifBase ):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._pendingConfMgrIds = self._normaliseListParam( params.get("pendingUsers", []) )
        self._pendingConfMgrs = []
        for email in self._pendingConfMgrIds:
            self._pendingConfMgrs.append(self._conf.getPendingQueuesMgr().getPendingConfManagersByEmail(email))
        self._send=params.has_key("confirm")
        self._confirmed=params.has_key("confirm") or params.has_key("cancel")


    def _process( self ):
        url=urlHandlers.UHConfModifPendingQueues.getURL(self._conf)
        url.addParam("tab","conf_managers")
        if self._pendingConfMgrs == []:
            self._redirect(url)
        if self._confirmed:
            if self._send:
                pendings=pendingQueues.PendingConfManagersHolder()
                for pss in self._pendingConfMgrs:
                    pendings._sendReminderEmail(pss)
            self._redirect(url)
        else:
            wp = conferences.WPConfModifPendingQueuesReminderConfMgrConfirm(self, self._conf, self._pendingConfMgrIds)
            return wp.display()

class RHConfModifPendingQueuesActionConfSubm:
    """
    class to select the action to do with the selected pending conference submitters
    """

    _uh = urlHandlers.UHConfModifPendingQueuesActionConfSubm

    def __init__(self, req):
        assert req is None

    def process(self, params):
        if 'remove' in params:
            return RHConfModifPendingQueuesRemoveConfSubm(None).process(params)
        elif 'reminder' in params:
            return RHConfModifPendingQueuesReminderConfSubm(None).process(params)
        return "no action to do"

class RHConfModifPendingQueuesRemoveConfSubm( RHConferenceModifBase ):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._pendingConfSubmIds = self._normaliseListParam( params.get("pendingUsers", []) )
        self._pendingConfSubms = []
        for id in self._pendingConfSubmIds:
            self._pendingConfSubms.extend(self._conf.getPendingQueuesMgr().getPendingConfSubmittersByEmail(id))
        self._remove=params.has_key("confirm")
        self._confirmed=params.has_key("confirm") or params.has_key("cancel")

    def _process( self ):
        url=urlHandlers.UHConfModifPendingQueues.getURL(self._conf)
        url.addParam("tab","conf_submitters")
        if self._pendingConfSubms == []:
            self._redirect(url)
        if self._confirmed:
            if self._remove:
                for ps in self._pendingConfSubms:
                    self._conf.getPendingQueuesMgr().removePendingConfSubmitter(ps)
            self._redirect(url)
        else:
            wp = conferences.WPConfModifPendingQueuesRemoveConfSubmConfirm(self, self._conf, self._pendingConfSubmIds)
            return wp.display()

class RHConfModifPendingQueuesReminderConfSubm( RHConferenceModifBase ):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._pendingConfSubmIds = self._normaliseListParam( params.get("pendingUsers", []) )
        self._pendingConfSubms = []
        for email in self._pendingConfSubmIds:
            self._pendingConfSubms.append(self._conf.getPendingQueuesMgr().getPendingConfSubmittersByEmail(email))
        self._send=params.has_key("confirm")
        self._confirmed=params.has_key("confirm") or params.has_key("cancel")


    def _process( self ):
        url=urlHandlers.UHConfModifPendingQueues.getURL(self._conf)
        url.addParam("tab","conf_submitters")
        if self._pendingConfSubms == []:
            self._redirect(url)
        if self._confirmed:
            if self._send:
                pendings=pendingQueues.PendingConfSubmittersHolder()
                for pss in self._pendingConfSubms:
                    pendings._sendReminderEmail(pss)
            self._redirect(url)
        else:
            wp = conferences.WPConfModifPendingQueuesReminderConfSubmConfirm(self, self._conf, self._pendingConfSubmIds)
            return wp.display()

class RHConfModifPendingQueuesActionSubm:
    """
    class to select the action to do with the selected pending contribution submitters
    """

    _uh = urlHandlers.UHConfModifPendingQueuesActionSubm

    def __init__(self, req):
        assert req is None

    def process(self, params):
        if 'remove' in params:
            return RHConfModifPendingQueuesRemoveSubm(None).process(params)
        elif 'reminder' in params:
            return RHConfModifPendingQueuesReminderSubm(None).process(params)
        return "no action to do"

class RHConfModifPendingQueuesRemoveSubm( RHConferenceModifBase ):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._pendingSubmIds = self._normaliseListParam( params.get("pendingUsers", []) )
        self._pendingSubms = []
        for id in self._pendingSubmIds:
            self._pendingSubms.extend(self._conf.getPendingQueuesMgr().getPendingSubmittersByEmail(id))
        self._remove=params.has_key("confirm")
        self._confirmed=params.has_key("confirm") or params.has_key("cancel")

    def _process( self ):
        url=urlHandlers.UHConfModifPendingQueues.getURL(self._conf)
        url.addParam("tab","submitters")
        if self._pendingSubms == []:
            self._redirect(url)
        if self._confirmed:
            if self._remove:
                for ps in self._pendingSubms:
                    self._conf.getPendingQueuesMgr().removePendingSubmitter(ps)
            self._redirect(url)
        else:
            wp = conferences.WPConfModifPendingQueuesRemoveSubmConfirm(self, self._conf, self._pendingSubmIds)
            return wp.display()

class RHConfModifPendingQueuesReminderSubm( RHConferenceModifBase ):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._pendingSubmIds = self._normaliseListParam( params.get("pendingUsers", []) )
        self._pendingSubms = []
        for email in self._pendingSubmIds:
            self._pendingSubms.append(self._conf.getPendingQueuesMgr().getPendingSubmittersByEmail(email))
        self._send=params.has_key("confirm")
        self._confirmed=params.has_key("confirm") or params.has_key("cancel")


    def _process( self ):
        url=urlHandlers.UHConfModifPendingQueues.getURL(self._conf)
        url.addParam("tab","submitters")
        if self._pendingSubms == []:
            self._redirect(url)
        if self._confirmed:
            if self._send:
                pendings=pendingQueues.PendingSubmittersHolder()
                for pss in self._pendingSubms:
                    pendings._sendReminderEmail(pss)
            self._redirect(url)
        else:
            wp = conferences.WPConfModifPendingQueuesReminderSubmConfirm(self, self._conf, self._pendingSubmIds)
            return wp.display()

class RHConfModifPendingQueuesActionMgr:
    """
    class to select the action to do with the selected pending submitters
    """

    _uh = urlHandlers.UHConfModifPendingQueuesActionMgr

    def __init__(self, req):
        assert req is None

    def process(self, params):
        if 'remove' in params:
            return RHConfModifPendingQueuesRemoveMgr(None).process(params)
        elif 'reminder' in params:
            return RHConfModifPendingQueuesReminderMgr(None).process(params)
        return "no action to do"

class RHConfModifPendingQueuesRemoveMgr( RHConferenceModifBase ):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._pendingMgrIds = self._normaliseListParam( params.get("pendingUsers", []) )
        self._pendingMgrs = []
        for id in self._pendingMgrIds:
            self._pendingMgrs.extend(self._conf.getPendingQueuesMgr().getPendingManagersByEmail(id))
        self._remove=params.has_key("confirm")
        self._confirmed=params.has_key("confirm") or params.has_key("cancel")


    def _process( self ):
        url=urlHandlers.UHConfModifPendingQueues.getURL(self._conf)
        url.addParam("tab","managers")
        if self._pendingMgrs == []:
            self._redirect(url)
        if self._confirmed:
            if self._remove:
                for ps in self._pendingMgrs:
                    self._conf.getPendingQueuesMgr().removePendingManager(ps)
            self._redirect(url)
        else:
            wp = conferences.WPConfModifPendingQueuesRemoveMgrConfirm(self, self._conf, self._pendingMgrIds)
            return wp.display()

class RHConfModifPendingQueuesReminderMgr( RHConferenceModifBase ):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._pendingMgrIds = self._normaliseListParam( params.get("pendingUsers", []) )
        self._pendingMgrs = []
        for email in self._pendingMgrIds:
            self._pendingMgrs.append(self._conf.getPendingQueuesMgr().getPendingManagersByEmail(email))
        self._send=params.has_key("confirm")
        self._confirmed=params.has_key("confirm") or params.has_key("cancel")


    def _process( self ):
        url=urlHandlers.UHConfModifPendingQueues.getURL(self._conf)
        url.addParam("tab","managers")
        if self._pendingMgrs == []:
            self._redirect(url)
        if self._confirmed:
            if self._send:
                pendings=pendingQueues.PendingManagersHolder()
                for pss in self._pendingMgrs:
                    pendings._sendReminderEmail(pss)
            self._redirect(url)
        else:
            wp = conferences.WPConfModifPendingQueuesReminderMgrConfirm(self, self._conf, self._pendingMgrIds)
            return wp.display()

class RHConfModifPendingQueuesActionCoord:
    """
    class to select the action to do with the selected pending submitters
    """

    _uh = urlHandlers.UHConfModifPendingQueuesActionCoord

    def __init__(self, req):
        assert req is None

    def process(self, params):
        if 'remove' in params:
            return RHConfModifPendingQueuesRemoveCoord(None).process(params)
        elif 'reminder' in params:
            return RHConfModifPendingQueuesReminderCoord(None).process(params)
        return "no action to do"

class RHConfModifPendingQueuesRemoveCoord( RHConferenceModifBase ):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._pendingCoordIds = self._normaliseListParam( params.get("pendingUsers", []) )
        self._pendingCoords = []
        for id in self._pendingCoordIds:
            self._pendingCoords.extend(self._conf.getPendingQueuesMgr().getPendingCoordinatorsByEmail(id))
        self._remove=params.has_key("confirm")
        self._confirmed=params.has_key("confirm") or params.has_key("cancel")


    def _process( self ):
        url=urlHandlers.UHConfModifPendingQueues.getURL(self._conf)
        url.addParam("tab", "coordinators")
        if self._pendingCoords == []:
            self._redirect(url)
        if self._confirmed:
            if self._remove:
                for ps in self._pendingCoords:
                    self._conf.getPendingQueuesMgr().removePendingCoordinator(ps)
            self._redirect(url)
        else:
            wp = conferences.WPConfModifPendingQueuesRemoveCoordConfirm(self, self._conf, self._pendingCoordIds)
            return wp.display()

class RHConfModifPendingQueuesReminderCoord( RHConferenceModifBase ):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._pendingCoordIds = self._normaliseListParam( params.get("pendingUsers", []) )
        self._pendingCoords = []
        for email in self._pendingCoordIds:
            self._pendingCoords.append(self._conf.getPendingQueuesMgr().getPendingCoordinatorsByEmail(email))
        self._send=params.has_key("confirm")
        self._confirmed=params.has_key("confirm") or params.has_key("cancel")


    def _process( self ):
        url=urlHandlers.UHConfModifPendingQueues.getURL(self._conf)
        url.addParam("tab", "coordinators")
        if self._pendingCoords == []:
            self._redirect(url)
        if self._confirmed:
            if self._send:
                pendings=pendingQueues.PendingCoordinatorsHolder()
                for pss in self._pendingCoords:
                    pendings._sendReminderEmail(pss)
            self._redirect(url)
        else:
            wp = conferences.WPConfModifPendingQueuesReminderCoordConfirm(self, self._conf, self._pendingCoordIds)
            return wp.display()

class RHConfAbstractFields( RHConfModifCFABase ):
    _uh = urlHandlers.UHConfModifCFAOptFld

    def _checkParams( self, params ):
        RHConfModifCFABase._checkParams( self, params )
        self._fieldId = params.get("fieldId", "")
        if self._fieldId.strip()!="":
            if not self._conf.getAbstractMgr().getAbstractFieldsMgr().hasField(self._fieldId):
                raise MaKaCError( _("The field that you are trying to enable/disable does not exist"))

    def _process( self ):
        if self._fieldId.strip() != "":
            if self._conf.getAbstractMgr().hasEnabledAbstractField(self._fieldId):
                self._conf.getAbstractMgr().disableAbstractField(self._fieldId)
            else:
                self._conf.getAbstractMgr().enableAbstractField(self._fieldId)
        self._redirect(urlHandlers.UHConfModifCFA.getURL(self._conf))


class RHConfRemoveAbstractField( RHConfModifCFABase ):
    _uh = urlHandlers.UHConfModifCFARemoveOptFld

    def _checkParams( self, params ):
        RHConfModifCFABase._checkParams( self, params )
        self._fieldIds = []
        if params.get("fieldId","") != "":
            self._fieldIds = self._normaliseListParam( params["fieldId"] )

    def _process( self ):
        for id in self._fieldIds:
            self._conf.getAbstractMgr().removeAbstractField(id)
        self._redirect(urlHandlers.UHConfModifCFA.getURL(self._conf))

class RHConfMoveAbsFieldUp( RHConfModifCFABase ):
    _uh = urlHandlers.UHConfModifCFAAbsFieldUp

    def _checkParams( self, params ):
        RHConfModifCFABase._checkParams( self, params )
        self._fieldId = params.get("fieldId", "")

    def _process( self ):
        if self._fieldId != "":
            self._conf.getAbstractMgr().moveAbsFieldUp(self._fieldId)
        self._redirect(urlHandlers.UHConfModifCFA.getURL(self._conf))

class RHConfMoveAbsFieldDown( RHConfModifCFABase ):
    _uh = urlHandlers.UHConfModifCFAAbsFieldDown

    def _checkParams( self, params ):
        RHConfModifCFABase._checkParams( self, params )
        self._fieldId = params.get("fieldId", "")

    def _process( self ):
        if self._fieldId != "":
            self._conf.getAbstractMgr().moveAbsFieldDown(self._fieldId)
        self._redirect(urlHandlers.UHConfModifCFA.getURL(self._conf))


class RHScheduleMoveEntryUp(RHConferenceModifBase):

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self._entry=self._conf.getSchedule().getEntryById(params.get("schEntryId",""))

    def _process(self):
        date=None
        if self._entry is not None:
            self._conf.getSchedule().moveUpEntry(self._entry)
            date=self._entry.getStartDate()
        if date is None:
            self._redirect(urlHandlers.UHConfModifSchedule.getURL(self._conf))
        else:
            self._redirect("%s#%s"%(urlHandlers.UHConfModifSchedule.getURL(self._conf),date.strftime("%Y-%m-%d")))


class RHScheduleMoveEntryDown(RHConferenceModifBase):

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self._entry=self._conf.getSchedule().getEntryById(params.get("schEntryId",""))

    def _process(self):
        date=None
        if self._entry is not None:
            self._conf.getSchedule().moveDownEntry(self._entry)
            date=self._entry.getStartDate()
        if date is None:
            self._redirect(urlHandlers.UHConfModifSchedule.getURL(self._conf))
        else:
            self._redirect("%s#%s"%(urlHandlers.UHConfModifSchedule.getURL(self._conf),date.strftime("%Y-%m-%d")))

class RHReschedule(RoomBookingDBMixin, RHConferenceModifBase):

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self._cancel=params.has_key("CANCEL")
        self._ok=params.has_key("OK")
        self._hour=params.get("hour","")
        self._minute=params.get("minute","")
        self._action=params.get("action","duration")
        self._fit= params.get("fit","noFit") == "doFit"
        self._targetDay=params.get("targetDay",None) #comes in format YYYYMMDD, ex: 20100317
        self._sessionId = params.get("sessionId", "")
        if self._targetDay is None:
            raise MaKaCError( _("Error while rescheduling timetable: not target day"))
        else:
            self._day=timezone(self._conf.getTimezone()).localize(datetime(int(params["targetDay"][0:4]),
                                                                           int(params["targetDay"][4:6]),
                                                                           int(params["targetDay"][6:8])))
        if self._ok:
            if self._hour.strip() == "" or self._minute.strip() == "":
                raise FormValuesError( _("Please write the time with the format HH:MM. For instance, 00:05 to indicate 'O hours' and '5 minutes'"))
            try:
                if int(self._hour) or int(self._hour):
                    pass
            except ValueError, e:
                raise FormValuesError( _("Please write a number to specify the time HH:MM. For instance, 00:05 to indicate 'O hours' and '5 minutes'"))

    def _process(self):
        if not self._cancel:
            if not self._ok:
                p = conferences.WPConfModifReschedule(self, self._conf, self._targetDay)
                return p.display()
            else:
                t = timedelta(hours=int(self._hour), minutes=int(self._minute))
        if self._sessionId:
            self._conf.getSessionById(self._sessionId).getSchedule().rescheduleTimes(self._action, t, self._day, self._fit)
            self._redirect("%s#%s" % (urlHandlers.UHSessionModifSchedule.getURL(self._conf.getSessionById(self._sessionId)), self._targetDay))
        else :
            self._conf.getSchedule().rescheduleTimes(self._action, t, self._day, self._fit)
            self._redirect("%s#%s" % (urlHandlers.UHConfModifSchedule.getURL(self._conf), self._targetDay))


class RHRelocate(RHConferenceModifBase):

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self._entry=None
        if params.has_key("contribId"):
            self._entry = self._conf.getContributionById(params.get("contribId",""))
            self._schEntry = self._entry.getSchEntry()
        elif params.has_key("schEntryId"):
            if params.has_key("sessionId") and params.has_key("slotId"):
                self._oldSch = self._conf.getSessionById(params.get("sessionId","")).getSlotById(params.get("slotId","")).getSchedule()
            else:
                self._oldSch = self._conf.getSchedule()
            try:
                self._schEntry = self._entry = self._oldSch.getEntryById(params.get("schEntryId",""))
            except:
                raise MaKaCError( _("Cannot find target item"))
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
                p=conferences.WPConfModifRelocate(self,self._conf, self._entry, self._targetDay)
                return p.display()
            else:
                if self._contribPlace.strip() != "":
                    if self._contribPlace!="conf":
                        s,ss=self._contribPlace.split(":")
                        session=self._conf.getSessionById(s)
                        if session is not None:
                            slot=session.getSlotById(ss)
                            if slot is not None:
                                self._schEntry.getSchedule().removeEntry(self._schEntry)
                                if isinstance(self._entry, conference.Contribution):
                                    self._entry.setSession(session)
                                slot.getSchedule().addEntry(self._schEntry, check=self._check)
                    else:
                        self._schEntry.getSchedule().removeEntry(self._schEntry)
                        self._conf.getSchedule().addEntry(self._schEntry, check=self._check)
        self._redirect("%s#%s"%(urlHandlers.UHConfModifSchedule.getURL(self._conf), self._targetDay))

class RHMaterialsAdd(RHSubmitMaterialBase, RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifAddMaterials

    def __init__(self, req):
        RHConferenceModifBase.__init__(self, req)
        RHSubmitMaterialBase.__init__(self)

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        RHSubmitMaterialBase._checkParams(self, params)


class RHMaterialsShow(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifShowMaterials

    def _process( self ):
        if self._target.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p.display()

        p = conferences.WPConfModifExistingMaterials( self, self._target )
        return p.display()

# ============================================================================
# === Room booking related ===================================================
# ============================================================================
from MaKaC.webinterface.rh.conferenceBase import RHConferenceSite

from MaKaC.rb_room import RoomBase
from MaKaC.rb_reservation import ReservationBase, RepeatabilityEnum
from MaKaC.rb_factory import Factory
from MaKaC.rb_location import ReservationGUID, RoomGUID, Location

# 0. Base Classes

from MaKaC.webinterface.rh.roomBooking import RHRoomBookingSearch4Rooms, RHRoomBookingCloneBooking, RHRoomBookingProtected
from MaKaC.webinterface.rh.roomBooking import RHRoomBookingRoomList
from MaKaC.webinterface.rh.roomBooking import RHRoomBookingBookingList
from MaKaC.webinterface.rh.roomBooking import RHRoomBookingRoomDetails
from MaKaC.webinterface.rh.roomBooking import RHRoomBookingBookingDetails
from MaKaC.webinterface.rh.roomBooking import RHRoomBookingBookingForm
from MaKaC.webinterface.rh.roomBooking import RHRoomBookingSaveBooking

# 0. RHConfModifRoomBookingChooseEvent

class RHConferenceModifRoomBookingBase( RoomBookingDBMixin, RHConferenceModifBase, RHRoomBookingProtected):

    def _checkProtection( self ):
        self._checkSessionUser()
        RHConferenceModifBase._checkProtection(self)
        RHRoomBookingProtected._checkSessionUser(self)

class RHConfModifRoomBookingChooseEvent( RHConferenceModifRoomBookingBase, RHRoomBookingSearch4Rooms ):
    _uh = urlHandlers.UHConfModifRoomBookingChooseEvent

    def _checkParams( self, params ):
        RHConferenceModifRoomBookingBase._checkParams( self, params )

        self._forNewBooking = True

    def _process( self ):

        p = conferences.WPConfModifRoomBookingChooseEvent( self )
        return p.display()

# 1. Searching

class RHConfModifRoomBookingSearch4Rooms( RHConferenceModifRoomBookingBase, RHRoomBookingSearch4Rooms ):
    _uh = urlHandlers.UHConfModifRoomBookingSearch4Rooms

    def _setDefaultFormValues( self ):
        """
        Sets default values for HTML forms.
        Uses event/session/contribution as an example.
        """

        # No example given? Fall back to general defaults
        if self._dontAssign:
            return

        if self._conf != None and self._conf.getRoom() and self._conf.getRoom().getName():
            self._eventRoomName = self._conf.getRoom().getName()

        # Copy values from   Session
        if self._conf is not None and self._assign2Session is not None:
            confSession = self._assign2Session
            session["rbDefaultStartDT"] = confSession.getAdjustedStartDate().replace(tzinfo=None)
            session["rbDefaultEndDT"] = confSession.getAdjustedEndDate().replace(tzinfo=None)
            if confSession.getStartDate().date() != confSession.getEndDate().date():
                session["rbDefaultRepeatability"] = RepeatabilityEnum.daily
            else:
                session["rbDefaultRepeatability"] = None
            session["rbDefaultBookedForName"] = self._getUser().getFullName() + " | " + confSession.getTitle()
            session["rbDefaultReason"] = "Session '" + confSession.getTitle() + "'"
            return

        # Copy values from   Contribution
        if self._conf is not None and self._assign2Contribution is not None:
            contrib = self._assign2Contribution
            session["rbDefaultStartDT"] = contrib.getAdjustedStartDate().replace(tzinfo=None)
            session["rbDefaultEndDT"] = contrib.getAdjustedEndDate().replace(tzinfo=None)
            if contrib.getStartDate().date() != contrib.getEndDate().date():
                session["rbDefaultRepeatability"] = RepeatabilityEnum.daily
            else:
                session["rbDefaultRepeatability"] = None
            session["rbDefaultBookedForName"] = self._getUser().getFullName() + " | " + contrib.getTitle()
            session["rbDefaultReason"] = "Contribution '" + contrib.getTitle() + "'"
            return

        # Copy values from   Conference / Meeting / Lecture
        if self._conf != None:
            conf = self._conf
            session["rbDefaultStartDT"] = conf.getAdjustedStartDate().replace(tzinfo=None)
            session["rbDefaultEndDT"] = conf.getAdjustedEndDate().replace(tzinfo=None)
            if conf.getStartDate().date() != conf.getEndDate().date():
                session["rbDefaultRepeatability"] = RepeatabilityEnum.daily
            else:
                session["rbDefaultRepeatability"] = None
            if self._getUser():
                session["rbDefaultBookedForName"] = self._getUser().getFullName() + " | " + conf.getTitle()
            else:
                session["rbDefaultBookedForName"] = conf.getTitle()
            session["rbDefaultReason"] = conf.getVerboseType() + " '" + conf.getTitle() + "'"
            return

    def _checkParams( self, params ):
        locator = locators.WebLocator()
        locator.setConference( params )
        self._conf = locator.getConference()

        RHRoomBookingSearch4Rooms._checkParams( self, params )
        self._forNewBooking = True

        if params.get('sessionId'):
            self._assign2Session = self._conf.getSessionById(params['sessionId'])
            session["rbAssign2Session"] = self._assign2Session.getLocator()
        else:
            self._assign2Session = None

        if params.get('contribId'):
            self._assign2Session = None
            self._assign2Contribution = self._conf.getContributionById(params['contribId'])
            session["rbAssign2Contribution"] = self._assign2Contribution.getLocator()
        else:
            self._assign2Contribution = None
        self._dontAssign = params.get('rbDontAssign') == "True"
        session["rbDontAssign"] = self._dontAssign

        self._setDefaultFormValues()

        RHConferenceModifRoomBookingBase._checkParams( self, params )

    def _process( self ):
        self._businessLogic()

        p = conferences.WPConfModifRoomBookingSearch4Rooms( self )
        return p.display()

# 2. List of...

class RHConfModifRoomBookingRoomList( RHConferenceModifRoomBookingBase, RHRoomBookingRoomList ):
    _uh = urlHandlers.UHConfModifRoomBookingRoomList

    def _checkParams( self, params ):
        RHConferenceModifRoomBookingBase._checkParams(self, params)
        RHRoomBookingRoomList._checkParams( self, params )

    def _process( self ):
        if self._target.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p.display()

        self._businessLogic()

        p = conferences.WPConfModifRoomBookingRoomList( self )
        return p.display()

class RHConfModifRoomBookingList( RHConferenceModifRoomBookingBase, RHRoomBookingBookingList ):
    _uh = urlHandlers.UHConfModifRoomBookingList

    def _checkParams( self, params ):
        RHRoomBookingBookingList._checkParams(self, params)
        RHConferenceModifRoomBookingBase._checkParams(self, params)

    def _process( self ):
        if self._target.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p.display()

        self._resvs = self._target.getRoomBookingList()
        for r in self._resvs:
            if r.getOwner() == None:
                r.setOwner( self._conf )

        p = conferences.WPConfModifRoomBookingList( self )
        return p.display()

# 3. Details of...

class RHConfModifRoomBookingRoomDetails( RHConferenceModifRoomBookingBase, RHRoomBookingRoomDetails ):
    _uh = urlHandlers.UHConfModifRoomBookingRoomDetails

    def _checkParams( self, params ):
        RHRoomBookingRoomDetails._checkParams(self, params)
        RHConferenceModifRoomBookingBase._checkParams(self, params)

    def _process( self ):
        self._businessLogic()
        p = conferences.WPConfModifRoomBookingRoomDetails( self )
        return p.display()

class RHConfModifRoomBookingDetails( RHConferenceModifRoomBookingBase, RHRoomBookingBookingDetails ):
    _uh = urlHandlers.UHConfModifRoomBookingDetails

    def _checkParams( self, params ):
        RHRoomBookingBookingDetails._checkParams( self, params )
        RHConferenceModifRoomBookingBase._checkParams(self, params)

    def _process( self ):
        self._businessLogic()
        self._resv.setOwner( self._conf )

        p = conferences.WPConfModifRoomBookingDetails( self )
        return p.display()

# 4. New ...

class RHConfModifRoomBookingBookingForm( RHConferenceModifRoomBookingBase, RHRoomBookingBookingForm ):
    _uh = urlHandlers.UHConfModifRoomBookingBookingForm

    def _checkParams( self, params ):
        RHRoomBookingBookingForm._checkParams( self, params )
        RHConferenceModifRoomBookingBase._checkParams(self, params)

    def _process( self ):
        self._businessLogic()
        self._candResv.setOwner( self._conf )
        p = conferences.WPConfModifRoomBookingBookingForm( self )
        return p.display()

class RHConfModifRoomBookingCloneBooking(RHConferenceModifRoomBookingBase, RHRoomBookingCloneBooking):
    def _checkParams(self, params):
        RHRoomBookingCloneBooking._checkParams(self, params)
        RHConferenceModifBase._checkParams(self, params)

    def _process( self ):
        self._redirect(urlHandlers.UHConfModifRoomBookingBookingForm.getURL(self._room))

class RHConfModifRoomBookingSaveBooking( RHConferenceModifRoomBookingBase, RHRoomBookingSaveBooking ):
    _uh = urlHandlers.UHConfModifRoomBookingSaveBooking

    def _checkParams( self, params ):
        RHConferenceModifRoomBookingBase._checkParams(self, params)
        RHRoomBookingSaveBooking._checkParams( self, params )

        # Assign room to event / session / contribution?
        self._assign2Session = None
        self._assign2Contribution = None
        if session.get('rbAssign2Session'):
            locator = locators.WebLocator()
            locator.setSession(session['rbAssign2Session'])
            self._assign2Session = locator.getObject()
        if session.get("rbAssign2Contribution"):
            locator = locators.WebLocator()
            locator.setContribution(session['rbAssign2Contribution'])
            self._assign2Contribution = locator.getObject()
        self._assign2Conference = None
        if not self._assign2Session and not self._assign2Contribution:
            if self._conf and not session.get("rbDontAssign"): # True or None
                self._assign2Conference = self._conf

    def _process( self ):
        self._businessLogic()

        if self._thereAreConflicts:
            url = urlHandlers.UHConfModifRoomBookingBookingForm.getURL( self._candResv.room )
            self._redirect( url )
        elif self._confirmAdditionFirst:
            p = conferences.WPConfModifRoomBookingConfirmBooking( self )
            return p.display()
        elif self._answer == 'No':
            url = urlHandlers.UHConfModifRoomBookingBookingForm.getURL(self._candResv.room)
            self._redirect(url)
        else:
            if self._formMode == FormMode.NEW:
                # Add it to event reservations list
                guid = ReservationGUID( Location.parse( self._candResv.locationName ), self._candResv.id )
                self._conf.addRoomBookingGuid( guid )

                # Set room for event / session / contribution (always only _one_ available)
                assign2 = self._assign2Conference or self._assign2Contribution or self._assign2Session
                if assign2:
                    croom = CustomRoom()         # Boilerplate class, has only 'name' attribute
                    croom.setName( self._candResv.room.name )
                    croom.setFullName(self._candResv.room.getFullName())
                    assign2.setRoom( croom )

            # Redirect
            self._candResv.setOwner( self._conf )
            url = urlHandlers.UHConfModifRoomBookingDetails.getURL( self._candResv )
            self._candResv.setOwner( None )
            self._redirect( url )



# ============================================================================
# === Badges related =========================================================
# ============================================================================

##------------------------------------------------------------------------------------------------------------
class RHConfBadgeBase(RHConferenceModifBase):

    def _checkProtection( self ):
        if not self._target.canManageRegistration(self.getAW().getUser()):
            RHConferenceModifBase._checkProtection(self)

"""
Badge Design and Printing classes
"""
class RHConfBadgePrinting(RHConfBadgeBase):
    """ This class corresponds to the screen where templates are
        listed and can be created, edited, deleted and tried.
        It always displays the list of templates; but we can
        arrive to this page in different scenarios:
        -A template has just been created (templateId = new template id, new = True). The template
        will be stored and the temporary backgrounds stored in the session object archived.
        -A template has been edited (templateId = existing template id, new = False or not set).
        The template will be updated and the temporary backgrounds stored in it, archived.
        -A template had been deleted (deleteTemplateId = id of the template to delete)
        -We were creating / editing a template but we pressed the "Cancel" button
        (templateId = id of the template that was being created / edited, Cancel = True).
        Temporary backgrounds (in the session object or in the template object) will be deleted.
    """

    def _checkParams(self, params):
        RHConfBadgeBase._checkParams(self, params)
        self.__templateId = params.get("templateId",None)
        self.__templateData = params.get("templateData",None)
        self.__deleteTemplateId = params.get("deleteTemplateId",None)
        self.__copyTemplateId = params.get("copyTemplateId",None)
        self.__new = params.get("new","False") == "True"
        self.__cancel = params.get("cancel","False") == "True"

    def _process(self):
        if self._target.isClosed():
            return conferences.WPConferenceModificationClosed(self, self._target).display()
        else:
            if self.__templateId and self.__templateData and not self.__deleteTemplateId:

                if self.__new:
                    self._target.getBadgeTemplateManager().storeTemplate(self.__templateId, self.__templateData)
                    key = "tempBackground-%s-%s" % (self._conf.id, self.__templateId)
                    filePaths = session.get(key)
                    if filePaths:
                        cfg = Config.getInstance()
                        tempPath = cfg.getUploadedFilesSharedTempDir()
                        for filePath in filePaths:
                            self._target.getBadgeTemplateManager().getTemplateById(self.__templateId).addTempBackgroundFilePath(filePath)
                            self._tempFilesToDelete.append(os.path.join(tempPath, filePath))
                        self._target.getBadgeTemplateManager().getTemplateById(self.__templateId).archiveTempBackgrounds(self._conf)
                else:
                    self._target.getBadgeTemplateManager().storeTemplate(self.__templateId, self.__templateData)

            elif self.__deleteTemplateId:
                self._target.getBadgeTemplateManager().deleteTemplate(self.__deleteTemplateId)

            elif self.__copyTemplateId:
                self._target.getBadgeTemplateManager().copyTemplate(self.__copyTemplateId)
            elif self.__cancel:
                if self._target.getBadgeTemplateManager().hasTemplate(self.__templateId):
                    self._target.getBadgeTemplateManager().getTemplateById(self.__templateId).deleteTempBackgrounds()
                else:
                    key = "tempBackground-%s-%s" % (self._conf.id, self.__templateId)
                    session.pop(key, None)

            if self._target.getId() == "default":
                p = admins.WPBadgeTemplates(self)
                url = urlHandlers.UHBadgeTemplates.getURL()
            else:
                p = conferences.WPConfModifBadgePrinting(self, self._target)
                url = urlHandlers.UHConfModifBadgePrinting.getURL(self._target)
            if request.method == 'POST':
                self._redirect(url)
            else:
                return p.display()


class RHConfBadgeDesign(RHConfBadgeBase):
    """ This class corresponds to the screen where templates are
        designed. We can arrive to this screen from different scenarios:
         -We are creating a new template (templateId = new template id, new = True)
         -We are editing an existing template (templateId = existing template id, new = False or not set)
    """

    def _checkParams(self, params):
        RHConfBadgeBase._checkParams(self, params)
        self.__templateId = params.get("templateId",None)
        new = params.get("new",'False')
        if new == 'False':
            self.__new = False
        else:
            self.__new = True
        self.__baseTemplate = params.get("baseTemplate",'blank')


    def _process(self):
        if self._target.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
        else:
            p = conferences.WPConfModifBadgeDesign(self, self._target, self.__templateId, self.__new, self.__baseTemplate)
        return p.display()

class RHConfBadgePrintingPDF(RHConfBadgeBase):
    """ This class is used to print the PDF from a badge template.
        There are 2 scenarios:
         -We are printing badges for all registrants (registrantList = 'all' or not set).
         -We are printing badges just for some registrants (registrantList = list of id's of registrants)
    """

    def _checkParams(self, params):
        """ Default values (1.5, etc...) are CERN's defaults in cm.
            These default values also appear in ConfModifBadgePDFOptions.tpl
            marginTop: top margin
            marginBottom: bottom margin
            marginLeft: left margin
            marginRight: right margin
            marginColumns: margin between columns
            marginRows: margin between rows
            keepPDFOptions: tells if we should keep the other params for the next time
                            by storing them in the database (in the conference object)
        """
        RHConfBadgeBase._checkParams(self, params)

        self.__templateId = params.get("templateId",None)

        #we retrieve the present PDF options of the conference in order to use
        #its values in case of input error
        self.__PDFOptions = self._target.getBadgeTemplateManager().getPDFOptions()

        self.__keepPDFOptions = params.get("keepPDFOptions", False)
        #in case of input error, this will be set to False

        try:
            self.__marginTop = float(params.get("marginTop",''))
        except ValueError:
            self.__marginTop = self.__PDFOptions.getTopMargin()
            self.__keepPDFOptions = False

        try:
            self.__marginBottom = float(params.get("marginBottom",''))
        except ValueError:
            self.__marginBottom = self.__PDFOptions.getBottomMargin()
            self.__keepPDFOptions = False

        try:
            self.__marginLeft = float(params.get("marginLeft",''))
        except ValueError:
            self.__marginLeft = self.__PDFOptions.getLeftMargin()
            self.__keepPDFOptions = False

        try:
            self.__marginRight = float(params.get("marginRight",''))
        except ValueError:
            self.__marginRight = self.__PDFOptions.getRightMargin()
            self.__keepPDFOptions = False

        try:
            self.__marginColumns = float(params.get("marginColumns",''))
        except ValueError:
            self.__marginColumns = self.__PDFOptions.getMarginColumns()
            self.__keepPDFOptions = False

        try:
            self.__marginRows = float(params.get("marginRows",''))
        except ValueError:
            self.__marginRows = self.__PDFOptions.getMarginRows()
            self.__keepPDFOptions = False

        self.__pagesize = params.get("pagesize",'A4')

        self.__drawDashedRectangles = params.get("drawDashedRectangles", False) is not False
        self.__landscape = params.get('landscape') == '1'

        self.__registrantList = params.get("registrantList","all")
        if self.__registrantList != "all":
            self.__registrantList = self.__registrantList.split(',')


    def _process(self):
        if self._target.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p
        else:
            if self._conf.getRegistrantsList() == []:
                return  _("There are no registrants, so no badges to print.")
            elif self.__templateId == None:
                return  _("There is no badge template selected for this conference.")

            if self.__keepPDFOptions:
                #we store the pdf options into the conference
                self.__PDFOptions.setTopMargin(self.__marginTop)
                self.__PDFOptions.setBottomMargin(self.__marginBottom)
                self.__PDFOptions.setLeftMargin(self.__marginLeft)
                self.__PDFOptions.setRightMargin(self.__marginRight)
                self.__PDFOptions.setMarginColumns(self.__marginColumns)
                self.__PDFOptions.setMarginRows(self.__marginRows)
                self.__PDFOptions.setPagesize(self.__pagesize)
                self.__PDFOptions.setDrawDashedRectangles(self.__drawDashedRectangles)
                self.__PDFOptions.setLandscape(self.__landscape)


            pdf = RegistrantsListToBadgesPDF(self._conf,
                                             self._conf.getBadgeTemplateManager().getTemplateById(self.__templateId),
                                             self.__marginTop,
                                             self.__marginBottom,
                                             self.__marginLeft,
                                             self.__marginRight,
                                             self.__marginColumns,
                                             self.__marginRows,
                                             self.__pagesize,
                                             self.__drawDashedRectangles,
                                             self.__registrantList,
                                             self.__landscape)
            return send_file('Badges.pdf', StringIO(pdf.getPDFBin()), 'PDF')


class RHConfBadgeSaveTempBackground(RHConfBadgeBase):
    """ This class is used to save a background as a temporary file,
        before it is archived. Temporary backgrounds are archived
        after pressing the "save" button.
        The temporary background filepath can be stored in the session
        object (if we are creating a new template and it has not been stored yet)
        or in the corresponding template if we are editing a template.
    """

    def _getNewTempFile( self ):
        cfg = Config.getInstance()
        tempPath = cfg.getUploadedFilesSharedTempDir()
        tempFileName = tempfile.mkstemp( suffix="IndicoBadgeBG.tmp", dir = tempPath )[1]
        return tempFileName

    def _saveFileToTemp(self, fs):
        fileName = self._getNewTempFile()
        fs.save(fileName)
        return os.path.split(fileName)[-1]

    def _checkParams(self, params):
        RHConfBadgeBase._checkParams(self, params)
        self.__templateId = params.get("templateId",None)
        try:
            self._tempFilePath = self._saveFileToTemp(params["file"])
        except AttributeError:
            self._tempFilePath = None

    def _process(self):
        if self._target.isClosed():
            return json.dumps({'status': 'error'}, textarea=True)
        else:
            if self._tempFilePath is not None:
                if self._conf.getBadgeTemplateManager().hasTemplate(self.__templateId):
                    backgroundId = self._conf.getBadgeTemplateManager().getTemplateById(self.__templateId).addTempBackgroundFilePath(self._tempFilePath)
                else:
                    key = "tempBackground-%s-%s" % (self._conf.id, self.__templateId)
                    value = session.get(key)
                    if value is None:
                        tempFilePathList = PersistentList()
                        tempFilePathList.append(self._tempFilePath)
                        session[key] = tempFilePathList
                        backgroundId = 0
                    else:
                        value.append(self._tempFilePath)
                        backgroundId = len(value) - 1
                        session.modified = True

                return json.dumps({
                    'status': 'OK',
                    'id': backgroundId,
                    'url': str(urlHandlers.UHConfModifBadgeGetBackground.getURL(self._conf, self.__templateId, backgroundId))
                }, textarea=True)

class RHConfBadgeGetBackground(RHConfBadgeBase):
    """ Class used to obtain a background in order to display it
        on the Badge Design screen.
        The background can be obtained from the archived files
        or from the temporary files.
    """

    def _checkParams(self, params):
        RHConfBadgeBase._checkParams(self, params)
        self.__templateId = params.get("templateId",None)
        self.__backgroundId = int(params.get("backgroundId",None))
        self.__width = int(params.get("width","-1"))
        self.__height = int(params.get("height","-1"))

    def __imageBin(self, image):
        mimetype = image.getFileType() or 'application/octet-stream'
        return send_file(image.getFileName(), image.getFilePath(), mimetype)

    def __fileBin(self, filePath):
        return send_file('tempBackground', filePath, 'application/octet-stream')

    def _process(self):
        if self._target.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p
        else:
            cfg = Config.getInstance()
            tempPath = cfg.getUploadedFilesSharedTempDir()
            if self._conf.getBadgeTemplateManager().hasTemplate(self.__templateId):
                isArchived, image = self._conf.getBadgeTemplateManager().getTemplateById(self.__templateId).getBackground(self.__backgroundId)
                if image is not None:
                    if isArchived:
                        return self.__imageBin(image)
                    else:
                        image = os.path.join(tempPath,image)
                        return self.__fileBin(image)

            else:
                key = "tempBackground-%s-%s" % (self._conf.id, self.__templateId)
                filePath = os.path.join(tempPath, session[key][int(self.__backgroundId)])
                return self.__fileBin(filePath)


# ============================================================================
# === Posters related ========================================================
# ============================================================================

##------------------------------------------------------------------------------------------------------------
"""
Poster Design and Printing classes
"""
class RHConfPosterPrinting(RHConferenceModifBase):
    """ This class corresponds to the screen where templates are
        listed and can be created, edited, deleted and tried.
        It always displays the list of templates; but we can
        arrive to this page in different scenarios:
        -A template has just been created (templateId = new template id, new = True). The template
        will be stored and the temporary backgrounds stored in the session object archived.
        -A template has been edited (templateId = existing template id, new = False or not set).
        The template will be updated and the temporary backgrounds stored in it, archived.
        -A template had been deleted (deleteTemplateId = id of the template to delete)
        -We were creating / editing a template but we pressed the "Cancel" button
        (templateId = id of the template that was being created / edited, Cancel = True).
        Temporary backgrounds (in the session object or in the template object) will be deleted.
    """

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.__templateId = params.get("templateId",None)
        self.__templateData = params.get("templateData",None)
        self.__deleteTemplateId = params.get("deleteTemplateId",None)
        self.__copyTemplateId = params.get("copyTemplateId",None)
        self.__bgPosition = params.get("bgPosition",None)
        self.__new = params.get("new","False") == "True"
        self.__cancel = params.get("cancel","False") == "True"


    def _process(self):
        if self._target.isClosed():
            return conferences.WPConferenceModificationClosed(self, self._target).display()
        else:
            if self.__templateId and self.__templateData and not self.__deleteTemplateId:
                if self.__new:
                # template is new
                    self._target.getPosterTemplateManager().storeTemplate(self.__templateId, self.__templateData)
                    key = "tempBackground-%s-%s" % (self._conf.id, self.__templateId)
                    filePaths = session.get(key)
                    if filePaths:
                        for filePath in filePaths:
                            self._target.getPosterTemplateManager().getTemplateById(self.__templateId).addTempBackgroundFilePath(filePath[0],filePath[1])
                        self._target.getPosterTemplateManager().getTemplateById(self.__templateId).archiveTempBackgrounds(self._conf)
                else:
                # template already exists
                    self._target.getPosterTemplateManager().storeTemplate(self.__templateId, self.__templateData)
            elif self.__deleteTemplateId:
                self._target.getPosterTemplateManager().deleteTemplate(self.__deleteTemplateId)
            elif self.__copyTemplateId:
                self._target.getPosterTemplateManager().copyTemplate(self.__copyTemplateId)
            elif self.__cancel:
                if self._target.getPosterTemplateManager().hasTemplate(self.__templateId):
                    self._target.getPosterTemplateManager().getTemplateById(self.__templateId).deleteTempBackgrounds()
                else:
                    fkey = "tempBackground-%s-%s" % (self._conf.id, self.__templateId)
                    session.pop(fkey, None)

            if self._target.getId() == "default":
                p = admins.WPPosterTemplates(self)
                url = urlHandlers.UHPosterTemplates.getURL()
            else:
                p = conferences.WPConfModifPosterPrinting(self, self._target)
                url = urlHandlers.UHConfModifPosterPrinting.getURL(self._target)
            if request.method == 'POST':
                self._redirect(url)
            else:
                return p.display()


class RHConfPosterDesign(RHConferenceModifBase):
    """ This class corresponds to the screen where templates are
        designed. We can arrive to this screen from different scenarios:
         -We are creating a new template (templateId = new template id, new = True)
         -We are editing an existing template (templateId = existing template id, new = False or not set)
    """

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.__templateId = params.get("templateId",None)
        new = params.get("new",'False')
        if new == 'False':
            self.__new = False
        else:
            self.__new = True
        self.__baseTemplate = params.get("baseTemplate",'blank')

    def _process(self):
        if self._target.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
        else:
            if (self._target.getId() == "default"):
                p = admins.WPPosterTemplateDesign(self, self._target, self.__templateId, self.__new)
            else:
                if self.__new == True and self.__baseTemplate != 'blank':
                    dconf = conference.CategoryManager().getDefaultConference()
                    templMan = self._target.getPosterTemplateManager()
                    newId = self.__templateId
                    dconf.getPosterTemplateManager().getTemplateById(self.__baseTemplate).clone(templMan, newId)
                    url = urlHandlers.UHConfModifPosterPrinting().getURL(self._target)
                    self._redirect(url)
                    return
                else:
                    p = conferences.WPConfModifPosterDesign(self, self._target, self.__templateId, self.__new, self.__baseTemplate)
        return p.display()

class RHConfPosterPrintingPDF(RHConferenceModifBase):
    """
        This class is used to print the PDF from a poster template.
    """
    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.__templateId = params.get("templateId",None)
        if self.__templateId == None:
            raise FormValuesError(_("Poster not selected"))
        if self.__templateId.find('global') != -1:
            self.__templateId = self.__templateId.replace('global','')
            self.__template = conference.CategoryManager().getDefaultConference().getPosterTemplateManager().getTemplateById(self.__templateId)
        else:
            self.__template = self._conf.getPosterTemplateManager().getTemplateById(self.__templateId)
        try:
            self.__marginH = int(params.get("marginH",'2'))
        except ValueError:
            self.__marginH = 2
        try:
            self.__marginV = int(params.get("marginV",'2'))
        except ValueError:
            self.__marginV = 2
        self.__pagesize = params.get("pagesize",'A4')


    def _process(self):
        if self._target.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p
        else:
            pdf = LectureToPosterPDF(self._conf,
                                             self.__template,
                                             self.__marginH,
                                             self.__marginV,
                                             self.__pagesize)

            return send_file('Poster.pdf', StringIO(pdf.getPDFBin()), 'PDF')


class RHConfPosterSaveTempBackground(RHConferenceModifBase):
    """ This class is used to save a background as a temporary file,
        before it is archived. Temporary backgrounds are archived
        after pressing the "save" button.
        The temporary background filepath can be stored in the session
        object (if we are creating a new template and it has not been stored yet)
        or in the corresponding template if we are editing a template.
    """

    def _getNewTempFile( self ):
        cfg = Config.getInstance()
        tempPath = cfg.getUploadedFilesSharedTempDir()
        tempFileName = tempfile.mkstemp( suffix="IndicoPosterBG.tmp", dir = tempPath )[1]
        return tempFileName

    def _saveFileToTemp(self, fs):
        fileName = self._getNewTempFile()
        fs.save(fileName)
        return os.path.split(fileName)[-1]

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.__templateId = params.get("templateId",None)

        self._bgPosition = params.get("bgPosition",None)

        try:
            self._tempFilePath = self._saveFileToTemp(params["file"])
        except AttributeError:
            self._tempFilePath = None

    def _process(self):
        if self._target.isClosed():
            return json.dumps({'status': 'error'}, textarea=True)
        else:
            if self._tempFilePath is not None:
                if self._conf.getPosterTemplateManager().hasTemplate(self.__templateId):
                # Save
                    backgroundId = self._conf.getPosterTemplateManager().getTemplateById(self.__templateId).addTempBackgroundFilePath(self._tempFilePath,self._bgPosition)
                else:
                # New
                    key = "tempBackground-%s-%s" % (self._conf.id, self.__templateId)
                    value = session.get(key)
                    if value is None:
                    # First background
                        tempFilePathList = PersistentList()
                        tempFilePathList.append((self._tempFilePath,self._bgPosition))
                        session[key] = tempFilePathList
                        backgroundId = 0
                    else:
                    # We have more
                        value.append((self._tempFilePath, self._bgPosition))
                        backgroundId = len(value) - 1
                        session.modified = True

                return json.dumps({
                    'status': 'OK',
                    'id': backgroundId,
                    'url': str(urlHandlers.UHConfModifPosterGetBackground.getURL(self._conf, self.__templateId, backgroundId)),
                    'pos': self._bgPosition
                }, textarea=True)


class RHConfPosterGetBackground(RHConferenceModifBase):
    """ Class used to obtain a background in order to display it
        on the Poster Design screen.
        The background can be obtained from the archived files
        or from the temporary files.
    """

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.__templateId = params.get("templateId",None)
        self.__backgroundId = int(params.get("backgroundId",None))
        self.__width = int(params.get("width","-1"))
        self.__height = int(params.get("height","-1"))

    def __imageBin(self, image):
        mimetype = image.getFileType() or 'application/octet-stream'
        return send_file(image.getFileName(), image.getFilePath(), mimetype)

    def __fileBin(self, filePath):
        return send_file('tempBackground', filePath, mimetype='application/octet-stream')

    def _process(self):

        if self._target.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p
        else:
            cfg = Config.getInstance()
            tempPath = cfg.getUploadedFilesSharedTempDir()

            if self._conf.getPosterTemplateManager().hasTemplate(self.__templateId):

                isArchived, image = self._conf.getPosterTemplateManager().getTemplateById(self.__templateId).getBackground(self.__backgroundId)

                if image is not None:
                    if isArchived:
                        return self.__imageBin(image)
                    else:
                        image = os.path.join(tempPath,image)
                        return self.__fileBin(image)

            else:
                key = "tempBackground-%s-%s" % (self._conf.id, self.__templateId)
                filePath = os.path.join(tempPath, session[key][int(self.__backgroundId)][0])
                return self.__fileBin(filePath)


class RHConfOffline(RHConferenceModifBase):

    def _checkProtection(self):
        RHConferenceModifBase._checkProtection(self)

    def _process(self):
        if not Config.getInstance().getOfflineStore():
            raise MaKaCError(_("This feature is not enabled"))
        return conferences.WPConfOffline(self, self._conf).display()
