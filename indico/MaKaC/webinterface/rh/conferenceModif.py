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

import os
from cStringIO import StringIO
import tempfile
import types
from flask import session, request, flash, redirect
from persistent.list import PersistentList
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta
from pytz import timezone
from BTrees.OOBTree import OOBTree
from werkzeug.exceptions import Forbidden
from MaKaC.webinterface.common.abstractDataWrapper import AbstractParam
import MaKaC.review as review
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.pages.conferences as conferences
from MaKaC.webinterface.general import normaliseListParam
from MaKaC.webinterface.rh.base import RHModificationBaseProtected
from MaKaC.webinterface.pages import admins
from MaKaC.webinterface.rh.conferenceBase import RHConferenceBase
from MaKaC.webinterface.rh.categoryDisplay import UtilsConference
from indico.core import signals
from indico.core.config import Config
from MaKaC.errors import MaKaCError, FormValuesError
from MaKaC.PDFinterface.conference import ConfManagerAbstractsToPDF, RegistrantsListToBadgesPDF, LectureToPosterPDF
from MaKaC.webinterface.common import AbstractStatusList, abstractFilters
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.common.xmlGen import XMLGen
from MaKaC.webinterface.common.abstractNotificator import EmailNotificator
import MaKaC.common.filters as filters
from MaKaC.common.contribPacker import ZIPFileHandler, AbstractPacker
from MaKaC.export.excel import AbstractListToExcel
from MaKaC.common import utils
from MaKaC.i18n import _
from indico.modules.events.requests.util import is_request_manager
from indico.util.signals import values_from_signal
from MaKaC.review import AbstractStatusSubmitted, AbstractStatusProposedToAccept, AbstractStatusProposedToReject
import MaKaC.webinterface.pages.abstracts as abstracts

from indico.util import json
from indico.web.flask.util import send_file, url_for
from indico.modules.attachments.controllers.event_package import AttachmentPackageGeneratorMixin

from markupsafe import Markup


class RHConferenceModifBase(RHConferenceBase, RHModificationBaseProtected):

    def _checkParams(self, params):
        RHConferenceBase._checkParams(self, params)

    def _checkProtection(self):
        RHModificationBaseProtected._checkProtection(self)

    def _displayCustomPage(self, wf):
        return None

    def _displayDefaultPage(self):
        return None

    def _process(self):
        wf = self.getWebFactory()
        if wf is not None:
            res = self._displayCustomPage(wf)
            if res is not None:
                return res
        return self._displayDefaultPage()


class RHConferenceModification(RHConferenceModifBase):
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


class RHConferenceModifManagementAccess( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfManagementAccess
    _tohttps = True

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        from MaKaC.webinterface.rh.reviewingModif import RCPaperReviewManager, RCReferee
        self._isPRM = RCPaperReviewManager.hasRights(self)
        self._isReferee = RCReferee.hasRights(self)
        self._requests_manager = is_request_manager(session.user)
        self._plugin_urls = values_from_signal(signals.event_management.management_url.send(self._conf),
                                               single_value=True)

    def _checkProtection(self):
        if not (self._isPRM or self._isReferee or self._requests_manager or self._plugin_urls):
            RHConferenceModifBase._checkProtection(self)

    def _process(self):
        url = None
        if self._conf.canModify(self.getAW()):
            url = urlHandlers.UHConferenceModification.getURL( self._conf )

        elif self._isPRM:
            url = urlHandlers.UHConfModifReviewingPaperSetup.getURL( self._conf )
        elif self._isReferee:
            url = urlHandlers.UHConfModifReviewingAssignContributionsList.getURL( self._conf )
        elif self._requests_manager:
            url = url_for('requests.event_requests', self._conf)
        elif self._plugin_urls:
            url = next(iter(self._plugin_urls), None)
        if not url:
            url = urlHandlers.UHConfManagementAccess.getURL( self._conf )

        self._redirect(url)


class RHConfDataModif(RHConferenceModifBase):
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


class RHConfPerformDataModif(RHConferenceModifBase):
    _uh = urlHandlers.UHConfPerformDataModif

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        if params.get("title", "").strip() =="" and not ("cancel" in params):
            raise FormValuesError("Please, provide a name for the event")
        self._cancel = params.has_key("cancel")

    def _process( self ):
        if not self._cancel:
            params = dict(self._getRequestParams(), keywords=request.form.getlist('keywords'))
            UtilsConference.setValues(self._conf, params)
        self._redirect( urlHandlers.UHConferenceModification.getURL( self._conf) )


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


class RHConfPerformCloning(RHConferenceModifBase, object):
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
        options = { "access"        : "cloneAccess"       in paramNames,
                    "keys"          : "cloneAccess"       in paramNames,
                    "authors"       : "cloneTimetable"    in paramNames,
                    "contributions" : "cloneTimetable"    in paramNames,
                    "subcontribs"   : "cloneTimetable"    in paramNames,
                    "sessions"      : "cloneTimetable"    in paramNames,
                    "tracks"        : "cloneTracks"       in paramNames,
                    "registration"  : "cloneRegistration" in paramNames,
                    "abstracts"     : "cloneAbstracts"    in paramNames,
                    "managing"      : self._getUser()
                    }
        #we notify the event in case any plugin wants to add their options
        if self._cancel:
            self._redirect( urlHandlers.UHConfClone.getURL( self._conf ) )
        elif self._confirm:
            if self._cloneType == "once" :
                newConf = self._conf.clone(self._date, options, userPerformingClone=self._aw._currentUser)
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
                    self._conf.clone(date, options, userPerformingClone=self._aw._currentUser)
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
                    self._conf.clone(date, options, userPerformingClone=self._aw._currentUser)
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
            self._redirect(self._conf.as_event.category.url)
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
                            self._conf.clone(od, options, userPerformingClone=self._aw._currentUser)
                        nbClones += 1
                else:
                    if params["order"] == "last":
                        if self._getLastDay(date,int(params["day"])) <= endDate:
                            if confirmed:
                                self._conf.clone(self._getLastDay(date, int(params["day"])), options,
                                                 userPerformingClone=self._aw._currentUser)
                            nbClones += 1
                    else:
                        new_date = (self._getFirstDay(date, int(params["day"])) +
                                    timedelta((int(params["order"]) - 1) * 7))
                        if new_date <= endDate:
                            if confirmed:
                                self._conf.clone(new_date, options, userPerformingClone=self._aw._currentUser)
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
                        self._conf.clone(self._getOpenDay(date, params["order"]), options,
                                         userPerformingClone=self._aw._currentUser)
                    nbClones += 1
                else:
                    if params["order"] == "last":
                        if confirmed:
                            self._conf.clone(self._getLastDay(date, int(params["day"])), options,
                                             userPerformingClone=self._aw._currentUser)
                        nbClones += 1
                    else:
                        if confirmed:
                            new_date = (self._getFirstDay(date, int(params["day"])) +
                                        timedelta((int(params["order"]) - 1) * 7))
                            self._conf.clone(new_date, options, userPerformingClone=self._aw._currentUser)
                        nbClones += 1
                month = int(date.month) + int(params["monthPeriod"])
                year = int(date.year)
                while month > 12:
                    month = month - 12
                    year = year + 1
                date = datetime(year,month,int(date.day), int(date.hour), int(date.minute))
        if confirmed:
            self._redirect(self._conf.as_event.category.url)
        else:
            return nbClones

####################################################################################


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
        sessionData["type"] = sessionData["acc_type"] = [str(ct.id) for ct in self._conf.as_event.contribution_types]
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
    def process(self, params):
        if params.has_key("newAbstract"):
            return RHNewAbstract().process(params)
        elif params.has_key("pdf"):
            return RHAbstractsToPDF().process(params)
        elif params.has_key("excel"):
            return RHAbstractsListToExcel().process(params)
        elif params.has_key("xml"):
            return RHAbstractsToXML().process(params)
        elif params.has_key("auth"):
            return RHAbstractsParticipantList().process(params)
        elif params.has_key("merge"):
            return RHAbstractsMerge().process(params)
        elif params.has_key("acceptMultiple"):
            return RHAbstractManagmentAcceptMultiple().process(params)
        elif params.has_key("rejectMultiple"):
            return RHAbstractManagmentRejectMultiple().process(params)
        elif params.has_key("PKGA"):
            return RHMaterialPackageAbstract().process(params)
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
                    _("No abstract has been specified"))
            else:
                self._abstracts = []
                for id in self._abstractIds:
                    abst = absMgr.getAbstractById(id)
                    if abst is None:
                        errorList.append(_("ID of abstract to be merged ('%s') is not valid") % id)
                    else:
                        statusKlass = abst.getCurrentStatus().__class__
                        if statusKlass in (review.AbstractStatusAccepted,
                                           review.AbstractStatusRejected,
                                           review.AbstractStatusWithdrawn,
                                           review.AbstractStatusDuplicated,
                                           review.AbstractStatusMerged):
                            label = AbstractStatusList.getInstance(
                            ).getCaption(statusKlass)
                            errorList.append(_("Abstract '%s' is in a state which does not allow merging (%s)") %
                                             (abst.getId(), label.upper()))
                        self._abstracts.append(abst)
            if self._targetAbsId == "":
                errorList.append(_("Invalid target abstract ID"))
            else:
                if self._targetAbsId in self._abstractIds:
                    errorList.append(_("Target abstract ID is among the abstract IDs to be merged"))
                self._targetAbs = absMgr.getAbstractById(self._targetAbsId)
                if self._targetAbs is None:
                    errorList.append(_("Invalid target abstract ID"))
                else:
                    statusKlass = self._targetAbs.getCurrentStatus().__class__
                    if statusKlass in (review.AbstractStatusAccepted,
                                       review.AbstractStatusRejected,
                                       review.AbstractStatusWithdrawn,
                                       review.AbstractStatusMerged,
                                       review.AbstractStatusDuplicated):
                        label = AbstractStatusList.getInstance(
                        ).getInstance().getCaption(statusKlass)
                        errorList.append(_("Target abstract is in a state which does not allow merging (%s)") %
                                         label.upper())

            if len(errorList) == 0:
                for abs in self._abstracts:
                    abs.mergeInto(self._getUser(), self._targetAbs,
                                  mergeAuthors=self._inclAuthors, comments=self._comments)
                    if self._doNotify:
                        abs.notify(EmailNotificator(), self._getUser())
                return self._redirect(urlHandlers.UHAbstractManagment.getURL(self._targetAbs))

        flash(Markup('Errors found: <ul>{}</ul>'.format(
                     ''.join('<li>{}</li>'.format(error) for error in errorList))), 'error')

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
                status = statusKlass(abstract, None)
                abstract.as_new.accepted_track_id = self._track.id if self._track else None
                abstract.as_new.accepted_type = cType
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
            if abstract.as_new.type:
                x.writeTag("ContributionType", abstract.as_new.type.name)
            else:
                x.writeTag("ContributionType", None)
            #x.writeTag("ContributionType", abstract.getContribType())

            for t in abstract.getTrackList():
                x.writeTag("Track", t.getTitle())
            accepted_track = abstract.getAcceptedTrack()
            if accepted_track:
                x.writeTag('AcceptedTrack', accepted_track.getTitle())

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

    def __init__(self):
        RHConfModifCFABase.__init__(self)
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


class RHMaterialPackage(RHConferenceModifBase, AttachmentPackageGeneratorMixin):

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self._contribIds = self._normaliseListParam(params.get("contributions", []))

    def _process(self):
        if not self._contribIds:
            flash(_('You did not select any contributions.'), 'warning')
            return redirect(url_for('event_mgmt.confModifContribList', self._conf))
        attachments = self._filter_by_contributions(self._contribIds, None)
        if not attachments:
            flash(_('The selected contributions do not have any materials.'), 'warning')
            return redirect(url_for('event_mgmt.confModifContribList', self._conf))
        return self._generate_zip_file(attachments, name_suffix=self.event_new.id)


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


# ============================================================================
# === Badges related =========================================================
# ============================================================================

##------------------------------------------------------------------------------------------------------------


class RHConfBadgeBase(RHConferenceModifBase):
    ROLE = 'registration'


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
            self.__registrantList = self.__registrantList.split(',') if self.__registrantList else []


    def _process(self):
        if self._target.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p
        else:
            if not self.__registrantList:
                return _("There are no registrations to print badges for.")
            elif self.__templateId is None:
                return _("There is no badge template selected for this conference.")

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
            return send_file('Badges.pdf', StringIO(pdf.getPDFBin()), 'PDF', inline=False)


class RHConfBadgeSaveTempBackground(RHConfBadgeBase):
    """ This class is used to save a background as a temporary file,
        before it is archived. Temporary backgrounds are archived
        after pressing the "save" button.
        The temporary background filepath can be stored in the session
        object (if we are creating a new template and it has not been stored yet)
        or in the corresponding template if we are editing a template.
    """

    def _checkProtection(self):
        if self._conf.id == 'default':
            if not session.user or not session.user.is_admin:
                raise Forbidden
        else:
            RHConfBadgeBase._checkProtection(self)

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

    def _checkProtection(self):
        if self._conf.id == 'default':
            if not session.user or not session.user.is_admin:
                raise Forbidden
        else:
            RHConfBadgeBase._checkProtection(self)

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
                    dconf = HelperMaKaCInfo.getMaKaCInfoInstance().getDefaultConference()
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
            self.__template = (HelperMaKaCInfo.getMaKaCInfoInstance().getDefaultConference()
                               .getPosterTemplateManager().getTemplateById(self.__templateId))
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

    def _checkProtection(self):
        if self._conf.id == 'default':
            if not session.user or not session.user.is_admin:
                raise Forbidden
        else:
            RHConferenceModifBase._checkProtection(self)

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

    def _checkProtection(self):
        if self._conf.id == 'default':
            if not session.user or not session.user.is_admin:
                raise Forbidden
        else:
            RHConferenceModifBase._checkProtection(self)

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
