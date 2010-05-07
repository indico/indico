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

import sys
import os
import stat
from copy import copy
import tempfile, types
from persistent.list import PersistentList
from datetime import datetime,timedelta
from pytz import timezone
import MaKaC.webinterface.common.timezones as convertTime
import MaKaC.common.timezoneUtils as timezoneUtils
from BTrees.OOBTree import OOBTree
from sets import Set
import MaKaC.webinterface.common.abstractDataWrapper as abstractDataWrapper
import MaKaC.review as review
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.materialFactories as materialFactories
import MaKaC.webinterface.displayMgr as displayMgr
import MaKaC.webinterface.internalPagesMgr as internalPagesMgr
import MaKaC.webinterface.pages.conferences as conferences
import MaKaC.webinterface.pages.reviewing as reviewing
import MaKaC.webinterface.pages.sessions as sessions
import MaKaC.user as user
import MaKaC.conference as conference
import MaKaC.schedule as schedule
import MaKaC.domain as domain
from MaKaC.webinterface.general import *
from MaKaC.webinterface.rh.base import RHModificationBaseProtected, RoomBookingDBMixin
from MaKaC.webinterface.rh.base import RH   # Strange conflict was here: this line vs nothing
from MaKaC.webinterface.pages import admins
from MaKaC.webinterface.rh.conferenceBase import RHConferenceBase, RHAlarmBase, RHSubmitMaterialBase
from MaKaC.webinterface.rh.categoryDisplay import UtilsConference
from MaKaC.webinterface.rh.conferenceDisplay import RHConferenceDisplay
from MaKaC.common import Config, info
from MaKaC.common.info import HelperMaKaCInfo
from MaKaC.errors import MaKaCError, FormValuesError,ModificationError
from MaKaC.PDFinterface.conference import ConfManagerAbstractsToPDF, ConfManagerContribsToPDF, RegistrantsListToBadgesPDF, LectureToPosterPDF
from MaKaC.webinterface.common import AbstractStatusList, abstractFilters
from MaKaC.webinterface import locators
from MaKaC.common.xmlGen import XMLGen
from MaKaC.webinterface.locators import WebLocator
from MaKaC.webinterface.common.abstractNotificator import EmailNotificator
import MaKaC.webinterface.common.registrantNotificator as registrantNotificator
import MaKaC.common.filters as filters
import MaKaC.webinterface.common.contribFilters as contribFilters
from MaKaC.webinterface.common.contribStatusWrapper import ContribStatusList
from MaKaC.webinterface.common.slotDataWrapper import Slot
from MaKaC.common.contribPacker import ZIPFileHandler,ContribPacker,ConferencePacker, ProceedingsPacker
from MaKaC.common.dvdCreation import DVDCreation
from MaKaC.participant import Participant
from MaKaC.conference import ContributionParticipation, Contribution, CustomRoom
from MaKaC.conference import SessionChair
from MaKaC.webinterface.mail import GenericMailer
from MaKaC.webinterface.mail import GenericNotification
from MaKaC.webinterface.wcomponents import WErrorMessage
from MaKaC.common import pendingQueues
from MaKaC.common import mail
import httplib
from MaKaC import booking
from MaKaC.export.excel import AbstractListToExcel, ParticipantsListToExcel
from MaKaC.common import utils
from MaKaC.i18n import _

from MaKaC.rb_location import CrossLocationDB, Location, CrossLocationQueries

from MaKaC.review import AbstractStatusSubmitted, AbstractStatusProposedToAccept, AbstractStatusProposedToReject
import MaKaC.webinterface.pages.abstracts as abstracts

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


class RHConferenceModificationClosed( RHConferenceModifBase ):

    def _process(self):
        if self._conf.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p.display()

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
        p=conferences.WPScreenDatesEdit(self,self._target)
        return p.display()

class RHConferenceModifKey( RHConferenceModifBase ):

    def _checkParams( self, params ):
        RHConferenceBase._checkParams(self, params )
        self._modifkey = params.get( "modifKey", "" ).strip()
        self._redirectURL = params.get("redirectURL","")

    def _checkProtection(self):
        modif_keys = self._getSession().getVar("modifKeys")
        if modif_keys == None:
            modif_keys = {}
        modif_keys[self._conf.getId()] = self._modifkey
        self._getSession().setVar("modifKeys",modif_keys)

        RHConferenceModifBase._checkProtection(self)

    def _process( self ):

        if self._redirectURL != "":
            url = self._redirectURL

#        elif self._conf.getType() == "conference":
#            url = urlHandlers.UHConferenceOtherViews.getURL( self._conf )
#        else:
#            url = urlHandlers.UHConferenceModification.getURL( self._conf )
        else:
            url = urlHandlers.UHConferenceDisplay.getURL( self._conf )
        self._redirect( url )

class RHConferenceModifManagementAccess( RHConferenceModifKey ):
    _uh = urlHandlers.UHConfManagementAccess

    def _checkParams(self, params):
        RHConferenceModifKey._checkParams(self, params)
        from MaKaC.webinterface.rh.reviewingModif import RCPaperReviewManager, RCAbstractManager, RCReferee
        from MaKaC.webinterface.rh.collaboration import RCVideoServicesManager
        from MaKaC.webinterface.rh.collaboration import RCCollaborationAdmin
        from MaKaC.webinterface.rh.collaboration import RCCollaborationPluginAdmin
        self._isRegistrar = self._target.isRegistrar( self._getUser() )
        self._isPRM = RCPaperReviewManager.hasRights(self)
        self._isAM = RCAbstractManager.hasRights(self)
        self._isReferee = RCReferee.hasRights(self)
        self._isVideoServicesManagerOrAdmin = (RCVideoServicesManager.hasRights(self, 'any') or
                                               RCCollaborationAdmin.hasRights(self) or
                                               RCCollaborationPluginAdmin.hasRights(self, plugins = 'any'))


    def _checkProtection(self):
        if not (self._isRegistrar or self._isPRM or self._isAM or self._isReferee or self._isVideoServicesManagerOrAdmin):
            RHConferenceModifKey._checkProtection(self)

    def _process( self ):

        if self._redirectURL != "":
            url = self._redirectURL

        elif self._conf.canModify(self.getAW()):
            url = urlHandlers.UHConferenceModification.getURL( self._conf )

        elif self._isRegistrar:
            url = urlHandlers.UHConfModifRegForm.getURL( self._conf )
        elif self._isPRM:
            url = urlHandlers.UHConfModifReviewingPaperSetup.getURL( self._conf )
        elif self._isAM:
            url = urlHandlers.UHConfModifReviewingAbstractSetup.getURL( self._conf )
        elif self._isReferee:
            url = urlHandlers.UHConfModifReviewingAssignContributionsList.getURL( self._conf )
        elif self._isVideoServicesManagerOrAdmin:
            from MaKaC.plugins.Collaboration.collaborationTools import CollaborationTools
            url = urlHandlers.UHConfModifCollaboration.getURL(self._conf, secure = CollaborationTools.isUsingHTTPS())

        else:
            url = urlHandlers.UHConfManagementAccess.getURL( self._conf )

        self._redirect( url )

class RHConferenceCloseModifKey( RHConferenceBase ):

    def _checkParams( self, params ):
        RHConferenceBase._checkParams(self, params )
        self._modifkey = params.get( "modifKey", "" ).strip()
        self._redirectURL = params.get("redirectURL","")

    def _process( self ):
        modif_keys = self._getSession().getVar("modifKeys")
        if modif_keys != None and modif_keys != {}:
            if modif_keys.has_key(self._conf.getId()) and self._conf.getModifKey() in modif_keys[self._conf.getId()]:
                del modif_keys[self._conf.getId()]
            self._getSession().setVar("modifKeys",modif_keys)
        if self._redirectURL != "":
            url = self._redirectURL
        else:
            url = urlHandlers.UHConferenceDisplay.getURL( self._conf )
        self._redirect( url )

class RHConferenceClose( RHConferenceBase ):
    _uh = urlHandlers.UHConferenceClose

    def _checkParams( self, params ):
        RHConferenceBase._checkParams(self, params )
        self._confirm = params.has_key( "confirm" )
        self._cancel = params.has_key( "cancel" )

    def _process( self ):

        if self._cancel:
            url = urlHandlers.UHConferenceModification.getURL( self._conf )
            self._redirect( url )
        elif self._confirm:
            self._target.setClosed(True)
            url = urlHandlers.UHConferenceModification.getURL( self._conf )
            self._redirect( url )
        else:
            return conferences.WPConfClosing( self, self._conf ).display()


class RHConferenceOpen( RHConferenceBase ):

    def _checkParams( self, params ):
        RHConferenceBase._checkParams(self, params )

    def _process( self ):
        self._target.setClosed(False)
        url = urlHandlers.UHConferenceModification.getURL( self._conf )
        self._redirect( url )


class RHConfDataModif( RoomBookingDBMixin, RHConferenceModifBase ):
    _uh = urlHandlers.UHConfDataModif

    def _displayCustomPage( self, wf ):
        return None

    def _displayDefaultPage( self ):
        p = conferences.WPConfDataModif( self, self._target )
        pars={}
        wf=self.getWebFactory()
        if wf is not None:
            pars["type"]=wf.getId()
        return p.display(**pars)


class RHConfPerformDataModif( RHConferenceModifBase ):
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


#class RHConfSelectChairs( RHConferenceModifBase ):
#    _uh = urlHandlers.UHConferenceSelectChairs
#
#    def _process( self ):
#        p = conferences.WPConfSelectChairs( self, self._conf )
#        return p.display( **self._getRequestParams() )
#

class RHChairNew(RHConferenceModifBase):
    _uh=urlHandlers.UHConfModChairNew

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self,params)
        self._action=""
        if params.has_key("ok"):
            self._action = "perform"
        elif params.has_key("cancel"):
            self._action = "cancel"

    def _newChair(self):
        chair=conference.ConferenceChair()
        p=self._getRequestParams()
        chair.setTitle(p.get("title",""))
        chair.setFirstName(p.get("name",""))
        chair.setFamilyName(p.get("surName",""))
        chair.setAffiliation(p.get("affiliation",""))
        chair.setEmail(p.get("email",""))
        chair.setAddress(p.get("address",""))
        chair.setPhone(p.get("phone",""))
        chair.setFax(p.get("fax",""))
        self._target.addChair(chair)
        #If the chairperson needs to be given management rights
        if p.get("manager", None):
            avl = user.AvatarHolder().match({"email":p.get("email","")})
            if avl:
                av = avl[0]
                self._target.grantModification(av)
            else:
                #Apart from granting the chairman, we add it as an Indico user
                self._target.grantModification(chair)

    def _process(self):
        if self._action!="":
            if self._action=="perform":
                self._newChair()
            url=urlHandlers.UHConferenceModification.getURL(self._target)
            self._redirect(url)
        else:
            p=conferences.WPModChairNew(self,self._conf)
            return p.display(**self._getRequestParams())


class RHConfRemoveChairs( RHConferenceModifBase ):
    _uh = urlHandlers.UHConferenceRemoveChairs

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        selChairId=self._normaliseListParam(params.get("selChair",[]))
        self._chairs=[]

        for id in selChairId:
            self._chairs.append(self._target.getChairById(id))

    def _process(self):
        for av in self._chairs:
            self._target.removeChair(av)
        self._redirect(urlHandlers.UHConferenceModification.getURL(self._target))


class RHChairEdit( RHConferenceModifBase ):

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self._chairId=params["chairId"]
        self._action=""
        if params.has_key("ok"):
            self._action = "perform"
        elif params.has_key("cancel"):
            self._action = "cancel"

    def _setChairData(self):
        c=self._target.getChairById(self._chairId)
        p = self._getRequestParams()
        c.setTitle(p.get("title",""))
        c.setFirstName(p.get("name",""))
        c.setFamilyName(p.get("surName",""))
        c.setAffiliation(p.get("affiliation",""))
        c.setEmail(p.get("email",""))
        c.setAddress(p.get("address",""))
        c.setPhone(p.get("phone",""))
        c.setFax(p.get("fax",""))
        if p.get("manager", None):
            avl = user.AvatarHolder().match({"email":p.get("email","")})
            if avl:
                av = avl[0]
                self._target.grantModification(av)
            else:
                self._target.grantModification(c)

    def _process(self):
        if self._action != "":
            if self._action == "perform":
                self._setChairData()
            url=urlHandlers.UHConferenceModification.getURL(self._target)
            self._redirect(url)
        else:
            c=self._target.getChairById(self._chairId)
            p = conferences.WPModChairEdit(self,self._target)
            return p.display(chair=c)


class RHConfAddMaterial( RHConferenceModifBase ):
    _uh = urlHandlers.UHConferenceAddMaterial

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        typeMat = params.get( "typeMaterial", "notype" )
        if typeMat=="notype" or typeMat.strip()=="":
            raise FormValuesError("Please choose a material type")
        self._mf = materialFactories.ConfMFRegistry().getById( typeMat )

    def _process( self ):
        if self._mf:
            if not self._mf.needsCreationPage():
                m = RHConfPerformAddMaterial.create( self._conf, self._mf, self._getRequestParams() )
                self._redirect( urlHandlers.UHMaterialModification.getURL( m ) )
                return
        p = conferences.WPConfAddMaterial( self, self._target, self._mf )
        return p.display()


class RHConfPerformAddMaterial( RHConferenceModifBase ):
    _uh = urlHandlers.UHConferencePerformAddMaterial

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        typeMat = params.get( "typeMaterial", "" )
        self._mf = materialFactories.ConfMFRegistry().getById( typeMat )

    @staticmethod
    def create( conf, matFactory, matData ):
        if matFactory:
            m = matFactory.create( conf )
        else:
            m = conference.Material()
            conf.addMaterial( m )
            m.setValues( matData )
        return m

    def _process( self ):
        m = self.create( self._conf, self._mf, self._getRequestParams() )
        self._redirect( urlHandlers.UHMaterialModification.getURL( m ) )


class RHConfRemoveMaterials( RHConferenceModifBase ):
    _uh = urlHandlers.UHConferenceRemoveMaterials

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        typeMat = params.get( "typeMaterial", "" )
        #self._mf = materialFactories.ConfMFRegistry.getById( typeMat )
        self._materialIds = self._normaliseListParam( params.get("materialId", []) )
        self._returnURL = params.get("returnURL","")

    def _process( self ):
        for id in self._materialIds:
            #Performing the deletion of special material types
            f = materialFactories.ConfMFRegistry().getById( id )
            if f:
                f.remove( self._target )
            else:
                #Performs the deletion of additional material types
                mat = self._target.getMaterialById( id )
                self._target.removeMaterial( mat )
        if self._returnURL != "":
            url = self._returnURL
        else:
            url = urlHandlers.UHConfModifMaterials.getURL( self._target )
        self._redirect( url )

#----------------------------------------------------------------

class RHConfSessionSlots( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModSessionSlots

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )

    def _process( self ):
        if self._target.getEnableSessionSlots() :
            for s in self._target.getSessionList() :
                if len(s.getSlotList()) > 1 :
                    raise FormValuesError( _("More then one slot defined for session '%s'. Cannot disable displaying multiple session slots.")%self._target.getTitle())
            self._target.disableSessionSlots()
        else :
            self._target.enableSessionSlots()
        self._redirect( urlHandlers.UHConferenceModification.getURL( self._target ) )

#----------------------------------------------------------------

class RHConfModifSchedule( RoomBookingDBMixin, RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModifSchedule

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )

        if params.get("view","").strip()!="":
            self._getSession().ScheduleView = params.get("view").strip()
        try:
            if self._getSession().ScheduleView:
                pass
        except AttributeError:
            self._getSession().ScheduleView=params.get("view","parallel")
        self._view=self._getSession().ScheduleView

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

##class RHConfModifScheduleGraphic( RHConferenceModifBase ):
##    _uh = urlHandlers.UHConfModifScheduleGraphic
##
##    def _process( self ):
##        if self._conf.isClosed():
##            p = conferences.WPConferenceModificationClosed( self, self._target )
##            return p.display()
##        else:
##            p = conferences.WPConfModifScheduleGraphic( self, self._target )
##            wf=self.getWebFactory()
##            if wf is not None:
##                p=wf.getConfModifSchedule( self, self._target )
##            return p.display()


class RHConfModifScheduleEntries( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModifScheduleEntries

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        params["sessions"] = self._normaliseListParam( params.get("session", []) )
        params["slots"] = self._normaliseListParam( params.get("slot", []) )
        params["entries"] = self._normaliseListParam( params.get("entries", []) )
        if params.get("session", None) is not None :
            del params["session"]
        if params.get("slot", None) is not None :
            del params["slot"]

    def _process( self ):
        params = self._getRequestParams()

        orginURL = urlHandlers.UHConfModifSchedule.getURL(self._conf)
        orginURL.addParam("slots",params["slots"])
        orginURL.addParam("sessions",params["sessions"])

        if len(params["entries"]) > 1 and not params["fired"] == _("Remove entries") :
            raise FormValuesError( _("For this action please select only one time schedule entry."))

        if params["fired"] == _("Add contribution") :
            if len(params["entries"]) == 0 :
                url = urlHandlers.UHConfModScheduleAddContrib.getURL(self._conf)
                url.addParam("targetDay","%s"%self._conf.getStartDate().date())
                self._redirect( url )
            elif not params["entries"][0][0:1] == "l" :
                raise FormValuesError( _("Contribution can be added only to conference or slot entry."))
            else :
                url = urlHandlers.UHSessionModScheduleAddContrib.getURL(self._conf)
                index = params["entries"][0].find("-")
                sessionId = params["entries"][0][1:index]
                slotId = params["entries"][0][index+1:]
                url.addParam("sessionId",sessionId)
                url.addParam("slotId",slotId)
                self._redirect( url )
        elif params["fired"] == _("New sub-contribution") :
            if len(params["entries"]) == 0 or not params["entries"][0][0:1] == "c" :
                raise FormValuesError( _("Sub-contribution can be added only to contribution entry."))
            else :
                url = urlHandlers.UHContribAddSubCont.getURL(self._conf)
                contribId = params["entries"][0][1:]
                url.addParam("contribId",contribId)
                self._redirect( url )
        elif params["fired"] == _("New break") :
            if len(params["entries"]) == 0 :
                url = urlHandlers.UHConfAddBreak.getURL(self._conf)
                url.addParam("targetDay","%s"%self._conf.getStartDate().date())
                self._redirect( url )
            elif not params["entries"][0][0:1] == "l" :
                raise FormValuesError( _("Break can be added only to conference or slot entry."))
            else :
                url = urlHandlers.UHSessionAddBreak.getURL(self._conf)
                index = params["entries"][0].find("-")
                sessionId = params["entries"][0][1:index]
                slotId = params["entries"][0][index+1:]
                url.addParam("sessionId",sessionId)
                url.addParam("slotId",slotId)
                self._redirect( url )
        elif params["fired"] == _("New contribution") :
            if len(params["entries"]) == 0 :
                url = urlHandlers.UHConfModScheduleNewContrib.getURL(self._conf)
                url.addParam("targetDay","%s"%self._conf.getStartDate().date())
                url.addParam("orginURL",orginURL)
                self._redirect( url )
            elif not params["entries"][0][0:1] == "l" :
                raise FormValuesError( _("Contribution can be added only to conference or slot entry."))
            else :
                #url = urlHandlers.UHSessionModScheduleNewContrib.getURL(self._conf)
                url = urlHandlers.UHConfModScheduleNewContrib.getURL(self._conf)
                index = params["entries"][0].find("-")
                sessionId = params["entries"][0][1:index]
                slotId = params["entries"][0][index+1:]
                slot = self._conf.getSessionById(sessionId).getSlotById(slotId)
                url.addParam("targetDay","%s"%slot.getStartDate().date())
                url.addParam("sessionId",sessionId)
                url.addParam("slotId",slotId)
                url.addParam("orginURL",orginURL)
                self._redirect( url )
        elif params["fired"] == _("New session") :
            if len(params["entries"]) == 0 :
                url = urlHandlers.UHConfAddSession.getURL(self._conf)
                url.addParam("targetDay","%s"%self._conf.getStartDate().date())
                self._redirect( url )
            else :
                raise FormValuesError( _("Session can be added only to conference."))
        elif params["fired"] == _("New slot") :
            if len(params["entries"]) == 0 or not params["entries"][0][0:1] == "s":
                raise FormValuesError( _("Slot can be added only to session."))
            else :
                url = urlHandlers.UHSessionModSlotNew.getURL(self._conf)
                index = params["entries"][0].find("-")
                sessionId = params["entries"][0][1:index]
                startDate = self._conf.getStartDate()
                url.addParam("slotDate","%s-%s-%s"%(startDate.day,startDate.month,startDate.year ))
                url.addParam("sessionId",sessionId)
                self._redirect( url )
        elif params["fired"] == _("Remove entries") :
            if len(params["entries"]) == 0 :
                raise FormValuesError( _("No entry selected for removal."))
            else :
                url = urlHandlers.UHConfModifScheduleEntriesRemove.getURL(self._conf)
                url.addParam("entries",params["entries"])
                self._redirect( url )
        elif params["fired"] == _("Reschedule") :
            if len(params["entries"]) == 0 :
                url = urlHandlers.UHConfModifReschedule.getURL(self._conf)
                targetDay = params.get("targetDay",self._conf.getStartDate().date())
                url.addParam("targetDay",targetDay)
                self._redirect( url )
            elif not params["entries"][0][0:1] == "l" :
                raise FormValuesError( _("Only a conference or a slot can be rescheduled."))
            else :
                index = params["entries"][0].find("-")
                sessionId = params["entries"][0][1:index]
                slotId = params["entries"][0][index+1:]
                url = urlHandlers.UHSessionModSlotCalc.getURL(self._conf)
                url.addParam("sessionId",sessionId)
                url.addParam("slotId",slotId)
                self._redirect( url )
        else :
            p = conferences.WPConfModifSchedule( self, self._target )
            wf=self.getWebFactory()
            if wf is not None:
                p=wf.getConfModifSchedule( self, self._target )
            return p.display(**params)


class RHConfModifScheduleEntriesRemove(RHConferenceModifBase):

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        params["entries"] = self._normaliseListParam( params.get("entries", []) )
        self._confirmed=params.has_key("confirm")
        self._cancel=params.has_key("cancel")

    def _process(self):
        params = self._getRequestParams()
        if not self._cancel:
            if not self._confirmed:
                p = conferences.WPPConfModifScheduleRemoveEtries(self,self._conf)
                return p.display(**params)

            for eId in params["entries"] :
                if eId[0:1] == "c" :
                    entry = self._conf.getContributionById(eId[1:]).getSchEntry()
                    entry.getSchedule().removeEntry(entry)
                    logInfo = entry.getOwner().getLogInfo()
                    logInfo["subject"] =  _("Removing contribution from timeschedule : %s")%entry.getOwner().getTitle()
                    self._conf.getLogHandler().logAction(logInfo,"Timetable/Contribution",self._getUser())

                elif eId[0:1] == "u" :
                    index = eId.find("-")
                    subcontribId = eId[index+1:]
                    contrib = self._conf.getContributionById(eId[1:index])
                    subcontrib = contrib.getSubContributionById(eId[index+1:])
                    logInfo = subcontrib.getLogInfo()
                    contrib.removeSubContribution(subcontrib)
                    logInfo["subject"] =  _("Removing subcontribution : %s")%subcontrib.getTitle()
                    self._conf.getLogHandler().logAction(logInfo,"Timetable/Subcontribution",self._getUser())

                elif eId[0:1] == "s" :
                    index = eId.find("-")
                    session = self._conf.getSessionById(eId[1:index])
                    self._conf.removeSession(session)
                    logInfo = session.getLogInfo()
                    logInfo["subject"] =  _("Removing subcontribution : %s")%session.getTitle()
                    self._conf.getLogHandler().logAction(logInfo,"Timetable/Subcontribution",self._getUser())

                elif eId[0:1] == "l" :
                    index = eId.find("-")
                    session = self._conf.getSessionById(eId[1:index])
                    slot = session.getSlotById(eId[index+1:])
                    logInfo = slot.getLogInfo()
                    session.removeSlot(slot)
                    logInfo["subject"] =  _("Removing slot : %s")%slot.getTitle()
                    self._conf.getLogHandler().logAction(logInfo,"Timetable/Slot",self._getUser())

                elif eId[0:1] == "b" :
                    index = eId.find("-")
                    if index == -1 :
                        entry = self._conf.getSchedule().getEntryById(eId[1:])
                        self._conf.getSchedule().removeEntry(entry)
                    else :
                        index2 = eId.find("-",index+1)
                        schedule = self._conf.getSessionById(eId[1:index]).getSlotById(eId[index+1:index2]).getSchedule()
                        entry = schedule.getEntryById(eId[index2+1:])
                        schedule.removeEntry(entry)

        self._redirect(urlHandlers.UHConfModifSchedule.getURL(self._conf))



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

###########################################################################################
class RHScheduleAddContrib(RHConferenceModifBase):

    def _checkParams(self,params):
        RHConferenceModifBase._checkParams(self,params)
        self._action=""
        ####################################
        # Fermi timezone awareness         #
        #  The params of targetDay have the#
        #  time relative to the conf tz.   #
        #  Need to convert to UTC          #
        ####################################
        tz = self._conf.getTimezone()
        sd=timezone(tz).localize(datetime(int(params["targetDay"][0:4]), \
           int(params["targetDay"][5:7]),int(params["targetDay"][8:])))
        self._targetDay=convertTime.convertTime(sd,'UTC')
        if params.has_key("OK"):
            self._action="ADD"
            self._selContribIdList=params.get("selContribs","").split(",")
            self._selContribIdList+=self._normaliseListParam(params.get("manSelContribs",[]))
        elif params.has_key("CANCEL"):
            self._action="CANCEL"

    def _process(self):
        tz = self._conf.getTimezone()
        if self._action=="ADD":
            for contribId in self._selContribIdList:
                if contribId.strip()=="":
                    continue
                contrib=self._target.getContributionById(contribId)
                if contrib is None:
                    continue
                d=self._target.getSchedule().calculateDayEndDate(self._targetDay)
                contrib.setStartDate(d)
                self._target.getSchedule().addEntry(contrib.getSchEntry())
            self._redirect(urlHandlers.UHConfModifSchedule.getURL(self._target))
        elif self._action=="CANCEL":
            self._redirect(urlHandlers.UHConfModifSchedule.getURL(self._target))
        else:
            p=conferences.WPModScheduleAddContrib(self,self._conf,self._targetDay)
            return p.display()

class RHMConfPerformAddContribution( RHConferenceModifBase ):
    _uh = urlHandlers.UHMConfPerformAddContribution

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._cancel = params.has_key("cancel")
        if not self._cancel:
            self._targetDay=datetime(int(params["targetDay"][0:4]),int(params["targetDay"][5:7]),int(params["targetDay"][8:]))
            self._stimehr = params["sHour"]
            self._stimemin = params["sMinute"]


    def _process( self ):
        if self._cancel:
            self._redirect( urlHandlers.UHConfModifSchedule.getURL( self._conf ) )
        else:
            contribution = conference.Contribution()
            self._conf.addContribution( contribution )
            contribution.setParent(self._conf)
            params = self._getRequestParams()
            if not params.has_key("check"):
                params["check"] = 1
            contribution.setValues( params,int(params['check']) )
            if self._stimehr is "":
                self._stimehr = 0
            if self._stimemin is "":
                self._stimemin = 0
            d=self._target.getSchedule().calculateDayEndDate(self._targetDay,hour=int(self._stimehr), min=int(self._stimemin))
            contribution.setStartDate(d)
            self._target.getSchedule().addEntry(contribution.getSchEntry(),int(params['check']))
            self._redirect(urlHandlers.UHConfModifSchedule.getURL(self._target))

#---------------------------------------------------------------------------

class RHConfAddSession( RoomBookingDBMixin, RHConferenceModifBase ):
    _uh = urlHandlers.UHConfAddSession

    def _checkParams(self,params):
        RHConferenceModifBase._checkParams( self, params )
        self._action=""
        self._day=None
        if params.has_key("OK"):
            self._action="CREATE"
        elif params.has_key("CANCEL"):
            self._action="CANCEL"
        elif params.has_key("performedAction") :
            self._action=params["performedAction"]
        else:
            if params.has_key("targetDay") :
                self._day=datetime(int(params["targetDay"][0:4]),int(params["targetDay"][5:7]),int(params["targetDay"][8:]))
                self._removeDefinedList("convener")
            else :
                preservedParams = self._getPreservedParams()
                self._day=datetime(int(preservedParams["sYear"]),int(preservedParams["sMonth"]),int(preservedParams["sDay"]))

        self._evt = None
        preservedParams = self._getPreservedParams()
        #raise "%s"%[params, preservedParams]
        for key in preservedParams.keys():
            if not key in params.keys():
                params[key] = preservedParams[key]
        #params.update(preservedParams)
        self._preserveParams( params )

    def _getErrors(self,params):
        l=[]
        title=str(params.get("title",""))
        if title.strip()=="":
            l.append( _("Session title cannot be empty"))
        return l

    def _create(self,params):
        if params["locationAction"] == "inherit":
            params["locationName"] = ""
        if params["roomAction"] == "inherit":
            params["roomName"] = ""
        elif params["roomAction"] == "exist":
            params["roomName"] = params.get("exists","")
        elif params["roomAction"] == "define":
            params["roomName"] = params.get( "bookedRoomName" )  or  params["roomName"]
        ###################################
        # Fermi timezone awareness        #
        ###################################
        conf_tz = self._conf.getTimezone()
        # Here we have to convert to UTC, but keep in mind that the
        # session timezone is the same as the conference.
        sDate=timezone(conf_tz).localize(datetime( int( params["sYear"] ),
                        int( params["sMonth"] ),
                        int( params["sDay"] ),
                        int( params["sHour"] ),
                        int( params["sMinute"] )))

        params["sDate"] = sDate.astimezone(timezone('UTC'))

        if params.get("eYear","") == "":
           eDate=timezone(conf_tz).localize(datetime( int( params["sYear"] ),
                           int( params["sMonth"] ),
                           int( params["sDay"] ),
                           int( params["eHour"] ),
                           int( params["eMinute"] )))
        else:
           eDate=timezone(conf_tz).localize(datetime( int( params["eYear"] ),
                           int( params["eMonth"] ),
                           int( params["eDay"] ),
                           int( params["eHour"] ),
                           int( params["eMinute"] )))
        params["eDate"] = eDate.astimezone(timezone('UTC'))
        ###################################
        # Fermi timezone awareness(end)   #
        ###################################
        s=conference.Session()
        s.setValues(params)
        self._conf.addSession(s)
        s.setScheduleType(params.get("tt_type",""))
        slot=conference.SessionSlot(s)
        slot.setStartDate(s.getStartDate())
        tz = timezone(self._conf.getTimezone())
        if s.getEndDate().astimezone(tz).date() > s.getStartDate().astimezone(tz).date():
            newEndDate = s.getStartDate().astimezone(tz).replace(hour=23,minute=59).astimezone(timezone('UTC'))
        else:
            newEndDate = s.getEndDate()
        dur = newEndDate - s.getStartDate()
        if dur > timedelta(days=1):
            dur = timedelta(days=1)
        slot.setDuration(dur=dur)
        s.addSlot(slot)

        convenerList = self._getDefinedList("convener")
        for convener in convenerList :
            s.addConvener(convener[0])
            if len(convener) > 1 and convener[1]:
                s._addCoordinatorEmail(convener[0].getEmail())
            if len(convener) > 2 and convener[2]:
                s.grantModification(convener[0])

        logInfo = s.getLogInfo()
        logInfo["subject"] =  _("Create new session: %s")%s.getTitle()
        self._conf.getLogHandler().logAction(logInfo,"Timetable/Session",self._getUser())

        self._removePreservedParams()
        self._removeDefinedList("convener")

    def _process( self ):
        errorList=[]
        params = self._getRequestParams()

        url=urlHandlers.UHConfModifSchedule.getURL(self._conf)
        if self._action=="CANCEL":
            self._removePreservedParams()
            self._removeDefinedList("convener")
            self._redirect(url)
            return
        elif self._action=="CREATE":
            errorList=self._getErrors(params)
            if len(errorList)==0:
                self._create(params)
                self._redirect(url)
                return
            else:
                raise MaKaCError( _("Session title cannot be empty"), _("Session"))
        elif self._action == "New convener":
            self._preserveParams(params)
            self._redirect(urlHandlers.UHConfNewSessionConvenerNew.getURL(self._conf))
        elif self._action == "Search convener":
            self._preserveParams(params)
            self._redirect(urlHandlers.UHConfNewSessionConvenerSearch.getURL(self._conf))
        elif self._action == "Remove conveners":
            self._removePersons(params, "convener")
        elif self._action == "Add as convener":
            self._preserveParams(params)
            url = urlHandlers.UHConfNewSessionPersonAdd.getURL(self._conf)
            url.addParam("orgin","added")
            url.addParam("typeName","convener")
            self._redirect(url)
        else :
            p = conferences.WPConfAddSession(self,self._target,self._day)

            params = copy(params)

            params["convenerDefined"] = self._getDefinedDisplayList("convener")
            params["convenerOptions"] = self._getPersonOptions("convener")
            params["errors"]=errorList
            return p.display(**params)

    def _getDefinedDisplayList(self, typeName):
         list = self._websession.getVar("%sList"%typeName)
         if list is None :
             return ""
         html = []
         counter = 0
         for person in list :
             text = """
                 <tr>
                     <td width="5%%"><input type="checkbox" name="%ss" value="%s"></td>
                     <td>&nbsp;%s</td>
                 </tr>"""%(typeName,counter,person[0].getFullName())
             html.append(text)
             counter = counter + 1
         return """
             """.join(html)

    def _getDefinedList(self, typeName):
        definedList = self._websession.getVar("%sList"%typeName)
        if definedList is None :
            return []
        return definedList

    def _setDefinedList(self, definedList, typeName):
        self._websession.setVar("%sList"%typeName,definedList)

    def _alreadyDefined(self, person, definedList):
        if person is None :
            return True
        if definedList is None :
            return False
        fullName = person.getFullName()
        for p in definedList :
            if p[0].getFullName() == fullName :
                return True
        return False

    def _removeDefinedList(self, typeName):
        self._websession.setVar("%sList"%typeName,None)

    def _getPreservedParams(self):
        params = self._websession.getVar("preservedParams")
        if params is None :
            return {}
        return params

    def _preserveParams(self, params):
        self._websession.setVar("preservedParams",params)

    def _removePreservedParams(self):
        self._websession.setVar("preservedParams",None)

    def _removePersons(self, params, typeName):
        persons = self._normaliseListParam(params.get("%ss"%typeName,[]))
        definedList = self._getDefinedList(typeName)
        personsToRemove = []
        for p in persons :
            if int(p) < len(definedList) or int(p) >= 0 :
                personsToRemove.append(definedList[int(p)])
        for person in personsToRemove :
            definedList.remove(person)
        self._setDefinedList(definedList,typeName)
        self._redirect(urlHandlers.UHConfAddSession.getURL(self._conf))

    def _personInDefinedList(self, typeName, person):
        list = self._websession.getVar("%sList"%typeName)
        if list is None :
            return False
        for p in list :
            if person.getFullName()+" "+person.getEmail() == p[0].getFullName()+" "+p[0].getEmail() :
                return True
        return False

    def _getPersonOptions(self, typeName):
        html = []
        names = []
        text = {}
        html.append("""<option value=""> </option>""")
        for session in self._conf.getSessionList() :
            for convener in session.getConvenerList() :
                name = convener.getFullNameNoTitle()
                if not name in names and not self._personInDefinedList(typeName, convener) :
                    text[name] = """<option value="d%s-%s">%s</option>"""%(session.getId(),convener.getId(),name)
                    names.append(name)
        for contribution in self._conf.getContributionList() :
            for speaker in contribution.getSpeakerList() :
                name = speaker.getFullNameNoTitle()
                if not name in names and not self._personInDefinedList(typeName, speaker):
                    text[name] = """<option value="s%s-%s">%s</option>"""%(contribution.getId(),speaker.getId(),name)
                    names.append(name)
            for author in contribution.getAuthorList() :
                name = author.getFullNameNoTitle()
                if not name in names and not self._personInDefinedList(typeName, author):
                    text[name] = """<option value="a%s-%s">%s</option>"""%(contribution.getId(),author.getId(),name)
                    names.append(name)
            for coauthor in contribution.getCoAuthorList() :
                name = coauthor.getFullNameNoTitle()
                if not name in names and not self._personInDefinedList(typeName, coauthor):
                    text[name] = """<option value="c%s-%s">%s</option>"""%(contribution.getId(),coauthor.getId(),name)
                    names.append(name)
        names.sort()
        for name in names:
            html.append(text[name])
        return "".join(html)

#-------------------------------------------------------------------------------------

class RHNewSessionConvenerSearch( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfNewSessionConvenerSearch

    def _checkParams( self, params):
        RHConferenceModifBase._checkParams(self,params)

    def _process( self ):
        params = self._getRequestParams()

        params["newButtonAction"] = str(urlHandlers.UHConfNewSessionConvenerNew.getURL())
        addURL = urlHandlers.UHConfNewSessionPersonAdd.getURL()
        addURL.addParam("orgin","selected")
        addURL.addParam("typeName","convener")
        params["addURL"] = addURL
        p = conferences.WPNewSessionConvenerSelect( self, self._target)
        return p.display(**params)

#-------------------------------------------------------------------------------------

class RHNewSessionConvenerNew( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfNewSessionConvenerNew

    def _checkParams( self, params):
        RHConferenceModifBase._checkParams(self,params)

    def _process( self ):
        p = conferences.WPNewSessionConvenerNew( self, self._target, {})

        return p.display()

#-------------------------------------------------------------------------------------

class RHNewSessionPersonAdd( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfNewSessionPersonAdd

    def _checkParams( self, params):
        RHConferenceModifBase._checkParams(self,params)
        self._typeName = params.get("typeName",None)
        if self._typeName  is None :
            raise MaKaCError( _("Type name of the person to add is not set."))

    def _process( self ):
        params = self._getRequestParams()
        self._errorList = []

        definedList = self._getDefinedList(self._typeName)
        if definedList is None :
            definedList = []

        if params.get("orgin","") == "new" :
            if params.get("ok",None) is None :
                self._redirect(urlHandlers.UHConfAddSession.getURL(self._conf))
                return
            else :

                if (params["email"]=="" and params.has_key("submissionControl")) or (not utils.validMail(params["email"]) and params["email"]!=""):
                    param={}
                    param["surNameValue"] = str(params["surName"])
                    param["nameValue"] = str(params["name"])
                    param["emailValue"] = str(params["email"])
                    param["titleValue"] = str(params["title"])
                    param["addressValue"] = str(params["address"])
                    param["affiliationValue"] = str(params["affiliation"])
                    param["phoneValue"] = str(params["phone"])
                    param["faxValue"] = str(params["fax"])
                    param["msg"] = "INSERT A VALID E-MAIL ADRESS"
                    if params.has_key("submissionControl"):
                        param["submissionControlValue"]="checked"

                    p=conferences.WPNewSessionConvenerNew(self, self._conf, param)
                    return p.display()

                person = SessionChair()
                person.setFirstName(params["name"])
                person.setFamilyName(params["surName"])
                person.setEmail(params["email"])
                person.setAffiliation(params["affiliation"])
                person.setAddress(params["address"])
                person.setPhone(params["phone"])
                person.setTitle(params["title"])
                person.setFax(params["fax"])
                if not self._alreadyDefined(person, definedList) :
                    definedList.append([person,params.has_key("coordinatorControl"),params.has_key("managerControl")])
                else :
                    self._errorList.append( _("%s has been already defined as %s of this session")%(person.getFullName(),self._typeName))

        elif params.get("orgin","") == "selected" :
            selectedList = self._normaliseListParam(self._getRequestParams().get("selectedPrincipals",[]))

            for s in selectedList :
                if s[0:8] == "*author*" :
                    auths = self._conf.getAuthorIndex()
                    selected = auths.getById(s[9:])[0]
                else :
                    ph = user.PrincipalHolder()
                    selected = ph.getById(s)
                if isinstance(selected, user.Avatar) :
                    person = SessionChair()
                    person.setDataFromAvatar(selected)
                    if not self._alreadyDefined(person, definedList) :
                        definedList.append([person,params.has_key("submissionControl")])
                    else :
                        self._errorList.append( _("%s has been already defined as %s of this session")%(person.getFullName(),self._typeName))

                elif isinstance(selected, user.Group) :
                    for member in selected.getMemberList() :
                        person = SessionChair()
                        person.setDataFromAvatar(member)
                        if not self._alreadyDefined(person, definedList) :
                            definedList.append([person,params.has_key("submissionControl")])
                        else :
                            self._errorList.append( _("%s has been already defined as %s of this session"))%(presenter.getFullName(),self._typeName)
                else :
                    person = SessionChair()
                    person.setTitle(selected.getTitle())
                    person.setFirstName(selected.getFirstName())
                    person.setFamilyName(selected.getFamilyName())
                    person.setEmail(selected.getEmail())
                    person.setAddress(selected.getAddress())
                    person.setAffiliation(selected.getAffiliation())
                    person.setPhone(selected.getPhone())
                    person.setFax(selected.getFax())
                    if not self._alreadyDefined(person, definedList) :
                        definedList.append([person,params.has_key("coordinatorControl"),params.has_key("managerControl")])
                    else :
                        self._errorList.append( _("%s has been already defined as %s of this session")%(person.getFullName(),self._typeName))

        elif params.get("orgin","") == "added" :
            preservedParams = self._getPreservedParams()
            chosen = preservedParams.get("%sChosen"%self._typeName,None)
            if chosen is None or chosen == "" :
                self._redirect(urlHandlers.UHConfAddSession.getURL(self._target))
                return
            index = chosen.find("-")

            chosenPerson = None

            if index == -1:
                ah = user.AvatarHolder()
                chosenPerson = SessionChair()
                chosenPerson.setDataFromAvatar(ah.getById(chosen))
            else:
                objectId = chosen[1:index]
                chosenId = chosen[index+1:len(chosen)]
                if chosen[0:1] == "d" :
                    object = self._conf.getSessionById(objectId)
                else :
                    object = self._conf.getContributionById(objectId)
                if chosen[0:1] == "s" :
                    chosenPerson = object.getSpeakerById(chosenId)
                elif chosen[0:1] == "a" :
                    chosenPerson = object.getAuthorById(chosenId)
                elif chosen[0:1] == "c" :
                    chosenPerson = object.getCoAuthorById(chosenId)
                elif chosen[0:1] == "d" :
                    chosenPerson = object.getConvenerById(chosenId)
            if chosenPerson is None :
                self._redirect(urlHandlers.UHConfModScheduleNewContrib.getURL(self._target))
                return
            person = SessionChair()
            person.setTitle(chosenPerson.getTitle())
            person.setFirstName(chosenPerson.getFirstName())
            person.setFamilyName(chosenPerson.getFamilyName())
            person.setEmail(chosenPerson.getEmail())
            person.setAddress(chosenPerson.getAddress())
            person.setAffiliation(chosenPerson.getAffiliation())
            person.setPhone(chosenPerson.getPhone())
            person.setFax(chosenPerson.getFax())
            if not self._alreadyDefined(person, definedList) :
                definedList.append([person,params.has_key("coordinatorControl"),params.has_key("managerControl")])
            else :
                self._errorList.append( _("%s has been already defined as %s of this session")%(person.getFullName(),self._typeName))
        else :
            self._redirect(urlHandlers.UHConfModifSchedule.getURL(self._target))
            return
        preservedParams = self._getPreservedParams()
        preservedParams["errorMsg"] = self._errorList
        self._preserveParams(preservedParams)
        self._websession.setVar("%sList"%self._typeName,definedList)

        self._redirect(urlHandlers.UHConfAddSession.getURL(self._conf))


    def _getDefinedList(self, typeName):
        definedList = self._websession.getVar("%sList"%typeName)
        if definedList is None :
            return []
        return definedList

    def _alreadyDefined(self, person, definedList):
        if person is None :
            return True
        if definedList is None :
            return False
        fullName = person.getFullName()
        for p in definedList :
            if p[0].getFullName() == fullName :
                return True
        return False

    def _getPreservedParams(self):
        params = self._websession.getVar("preservedParams")
        if params is None :
            return {}
        return params

    def _preserveParams(self, params):
        self._websession.setVar("preservedParams",params)
    def _removePreservedParams(self):
        self._websession.setVar("preservedParams",None)

#-------------------------------------------------------------------------------------


class RHSlotRem(RHConferenceModifBase):

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self._session=self._conf.getSessionById(params["sessionId"])
        self._slotId=params.get("slotId","")
        self._confirmed=params.has_key("confirm")
        self._cancel=params.has_key("cancel")

    def _process(self):
        if not self._cancel:
            slot=self._session.getSlotById(self._slotId)
            if not self._confirmed:
                p=conferences.WPModSlotRemConfirmation(self,slot)
                return p.display()
            self._session.removeSlot(slot)
        self._redirect(urlHandlers.UHConfModifSchedule.getURL(self._conf))

class RHScheduleSessionMove(RHConferenceModifBase):

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self._session=self._conf.getSessionById(params["sessionId"])
        self._confirmed=params.has_key("ok")
        self._date = None
        #
        # The date supplied is in the conference TZ, must convert to UTC
        #
        if self._confirmed:
            tz = self._session.getOwner().getTimezone()
            d = timezone(tz).localize(datetime(int(params["sYear"]),
                                        int(params["sMonth"]),
                                        int(params["sDay"]),
                                        int(params["sHour"]),
                                        int(params["sMinute"])))
            self._date=d.astimezone(timezone('UTC'))
        self._cancel=params.has_key("cancel")

    def _process(self):
        if not self._cancel:
            if not self._confirmed:
                p=conferences.WPModSessionMoveConfirmation(self,self._session)
                return p.display()
            self._session.move(self._date)
        self._redirect(urlHandlers.UHConfModifSchedule.getURL(self._conf))

class RHSessionRem(RHConferenceModifBase):

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self._session=self._conf.getSessionById(params["sessionId"])
        self._confirmed=params.has_key("confirm")
        self._cancel=params.has_key("cancel")

    def _process(self):
        if not self._cancel:
            if not self._confirmed:
                p=conferences.WPModSessionRemConfirmation(self,self._session)
                return p.display()
            logInfo = self._session.getLogInfo()
            logInfo["subject"] = "Deleted session: %s"%self._session.getTitle()
            self._conf.getLogHandler().logAction(logInfo,"Timetable/Session",self._getUser())
            isMeeting = (self._conf.getType() == "meeting")
            self._conf.removeSession(self._session, deleteContributions = isMeeting)
        self._redirect(urlHandlers.UHConfModifSchedule.getURL(self._conf))


class RHConfAddBreak( RoomBookingDBMixin, RHConferenceModifBase ):
    _uh=urlHandlers.UHConfAddBreak

    def _checkParams(self,params):
        RHConferenceModifBase._checkParams(self, params)
        ##########################################
        # Fermi timezone awareness               #
        ##########################################
        self._day=datetime(int(params["targetDay"][0:4]),int(params["targetDay"][5:7]),int(params["targetDay"][8:]))
        self._evt = None
        conf_tz = self._conf.getTimezone()
        ##########################################
        # Fermi timezone awareness(end)          #
        ##########################################

    def _process(self):
        p=conferences.WPConfAddBreak(self,self._conf,self._day)
        return p.display()


class RHConfPerformAddBreak(RHConferenceModifBase):
    _uh=urlHandlers.UHConfPerformAddBreak

    def _checkParams(self,params):
        RHConferenceModifBase._checkParams(self,params)
        self._cancel=params.has_key("CANCEL")

    def _process( self ):
        if not self._cancel:
            params = self._getRequestParams()
            if params["locationAction"] == "inherit":
                params["locationName"] = ""
            if params["roomAction"] == "inherit":
                params["roomName"] = ""
            b=schedule.BreakTimeSchEntry()
            params = self._getRequestParams()
            b.setValues(params,tz=self._conf.getTimezone())
            self._target.getSchedule().addEntry(b)
        self._redirect(urlHandlers.UHConfModifSchedule.getURL(self._conf))


class RHConfModifyBreak( RoomBookingDBMixin, RHConferenceModifBase ):
    _uh=urlHandlers.UHConfModifyBreak

    def _checkParams(self,params):
        RHConferenceModifBase._checkParams(self,params)
        if params.get("schEntryId","").strip()=="":
            raise Exception( _("schedule entry order number not set"))
        self._break=self._evt=self._conf.getSchedule().getEntryById(params["schEntryId"])

        params["days"] = params.get("day", "all")
        if params.get("day", None) is not None :
            del params["day"]

    def _process(self):
        p=conferences.WPConfModifyBreak(self,self._conf,self._break)
        return p.display(**self._getRequestParams())


class RHConfPerformModifyBreak( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfPerformModifyBreak

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._check = int(params.get("check",1))
        self._moveEntries = int(params.get("moveEntries",0))
        if params.get( "schEntryId", "" ).strip() == "":
            raise Exception( _("schedule entry order number not set"))
        self._break=self._conf.getSchedule().getEntryById(params["schEntryId"])
        if params.get( "bookedRoomName" ):
            params["roomName"] = params.get( "bookedRoomName" )

    def _process( self ):
        params = self._getRequestParams()
        if "CANCEL" not in params:
            self._break.setValues( params, self._check, self._moveEntries, tz=self._conf.getTimezone() )
        self._redirect( urlHandlers.UHConfModifSchedule.getURL( self._conf ) )


class RHConfDelSchItems( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfDelSchItems

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._entries=[]
        for id in self._normaliseListParam(params.get("schEntryId",[])):
            entry=self._conf.getSchedule().getEntryById(id)
            if entry is not None:
                self._entries.append(entry)

    def _process(self):
        type = self._conf.getType()
        for e in self._entries:
            self._target.getSchedule().removeEntry(e)
            if type == "meeting":
                if isinstance(e.getOwner(), Contribution) :
                    logInfo = e.getOwner().getLogInfo()
                    logInfo["subject"] =  _("Deleted contribution: %s")%e.getOwner().getTitle()
                    self._conf.getLogHandler().logAction(logInfo,"Timetable/Contribution",self._getUser())
                    e.getOwner().delete()
            else:
                if isinstance(e.getOwner(), Contribution) :
                    logInfo = e.getOwner().getLogInfo()
                    logInfo["subject"] =  _("Unscheduled contribution: %s")%e.getOwner().getTitle()
                    self._conf.getLogHandler().logAction(logInfo,"Timetable/Contribution",self._getUser())

        self._redirect(urlHandlers.UHConfModifSchedule.getURL(self._conf))



#class RHSchEditBreak(RHConferenceModifBase):
#
#    def _checkParams(self,params):
#        RHConferenceModifBase._checkParams(self,params)
#        self._break=self._conf.getSchedule().getEntryById(params.get("schEntryId",""))
#        self._action=""
#        if params.has_key("OK"):
#            self._action="GO"
#        elif params.has_key("CANCEL"):
#            self._action="CANCEL"
#
#    def _process(self):
#        url=urlHandlers.UHConfModifSchedule.getURL(self._conf)
#        if self._action=="GO":
#            self._break.setValues(self._getRequestParams())
#            self._redirect(url)
#            return
#        elif self._action=="CANCEL":
#            self._redirect(url)
#            return
#        else:
#            p=conferences.WPModSchEditBreak(self,self._break)
#            return p.display()


class RHSchEditContrib(RHConferenceModifBase):

    def _checkParams(self,params):
        RHConferenceModifBase._checkParams(self,params)
        self._check = int(params.get("check",1))
        self._moveEntries = int(params.get("moveEntries",0))
        self._contrib=self._conf.getContributionById(params.get("contribId",""))
        self._action=""
        if params.has_key("OK"):
            self._action="GO"
        elif params.has_key("CANCEL"):
            self._action="CANCEL"

    def _process(self):
        url=urlHandlers.UHConfModifSchedule.getURL(self._conf)
        if self._action=="GO":
            params = self._getRequestParams()
            if params.get("locationAction","") == "inherit":
                params["locationName"] = ""
            if params.get("roomAction", "") == "inherit":
                params["roomName"] = ""
            self._contrib.setValues(params, self._check, self._moveEntries)
            self._redirect(url)
        elif self._action=="CANCEL":
            self._redirect(url)
        else:
            p=conferences.WPModSchEditContrib(self,self._contrib)
            return p.display()


class RHSchEditSlot(RHConferenceModifBase):

    def _checkParams(self,params):
        RHConferenceModifBase._checkParams(self,params)
        self._check = int(params.get("check",1))
        self._moveEntries = int(params.get("moveEntries",0))
        self._session=self._conf.getSessionById(params.get("sessionId",""))
        self._slot=self._session.getSlotById(params.get("slotId",""))
        self._action = ""
        if params.get("CANCEL", None) is not None:
            self._action = "cancel"
        elif params.get("OK", None) is not None:
            self._action = "submit"

    def _process(self):
        params = self._getRequestParams()
        url = urlHandlers.UHConfModifSchedule.getURL(self._conf)
        if params.get("orginURL","") != "" :
            url = params.get("orginURL",url)
        if self._action == "cancel":
            self._redirect(url)
        elif self._action == "submit":
            params["id"]=self._slot.getId()
            params["session"]=self._slot.getSession()
            params["conveners"]=self._slot.getOwnConvenerList()[:]
            params["title"]=self._slot.getTitle()
            params["move"]=1
            location = self._slot.getOwnLocation()
            if location is not None:
                params["locationName"]=location.getName()
                params["locationAddress"]=location.getAddress()
            params["contribDuration"]=self._slot.getContribDuration()
            self._slot.setValues( params, self._check, self._moveEntries )
            self._redirect( url )
        else:
            slotData=Slot()
            slotData.mapSlot(self._slot)
            p = conferences.WPModSchEditSlot(self, slotData)
            return p.display(**params)


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
        if params["visibility"] == "PRIVATE":
            self._protectConference = 1
        elif params["visibility"] == "PUBLIC":
            self._protectConference = 0
        elif params["visibility"] == "ABSOLUTELY PUBLIC":
            self._protectConference = -1

    def _process( self ):
        self._conf.setProtection( self._protectConference )
        self._redirect( urlHandlers.UHConfModifAC.getURL( self._conf ) )


class RHConfSetAccessKey( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfSetAccessKey

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._accessKey = params.get( "accessKey", "")

    def _process( self ):
        self._conf.setAccessKey( self._accessKey )
        self._redirect( urlHandlers.UHConfModifAC.getURL( self._conf ) )


class RHConfSetModifKey( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfSetModifKey

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._modifKey = params.get( "modifKey", "")

    def _process( self ):
        self._conf.setModifKey( self._modifKey )
        self._redirect( urlHandlers.UHConfModifAC.getURL( self._conf ) )


class RHConfSelectAllowed( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfSelectAllowed

    def _process( self ):
        p = conferences.WPConfSelectAllowed( self, self._conf )
        return p.display( **self._getRequestParams() )


class RHConfAddAllowed( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfAddAllowed

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        selAllowedId = self._normaliseListParam( params.get( "selectedPrincipals", [] ) )
        #ah = user.AvatarHolder()
        self._allowed = []
        ph = user.PrincipalHolder()
        for id in selAllowedId:
            p = ph.getById( id )
            if p:
                self._allowed.append( p )



    def _process( self ):
        for av in self._allowed:
            self._target.grantAccess( av )
        self._redirect( urlHandlers.UHConfModifAC.getURL( self._conf) )


class RHConfRemoveAllowed( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfRemoveAllowed

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        selAllowedId = self._normaliseListParam( params.get( "selectedPrincipals", [] ) )
        #ah = user.AvatarHolder()
        ph = user.PrincipalHolder()
        self._allowed = []
        for id in selAllowedId:
            self._allowed.append( ph.getById( id ) )

    def _process( self ):
        for av in self._allowed:
            self._target.revokeAccess( av )
        self._redirect( urlHandlers.UHConfModifAC.getURL( self._conf ) )


class RHConfAddDomains( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfAddDomain

    def _process( self ):
        params = self._getRequestParams()
        if ("addDomain" in params) and (len(params["addDomain"])!=0):
            dh = domain.DomainHolder()
            for domId in self._normaliseListParam( params["addDomain"] ):
                self._target.requireDomain( dh.getById( domId ) )
        self._redirect( urlHandlers.UHConfModifAC.getURL( self._target ) )


class RHConfRemoveDomains( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfRemoveDomain

    def _process( self ):
        params = self._getRequestParams()
        if ("selectedDomain" in params) and (len(params["selectedDomain"])!=0):
            dh = domain.DomainHolder()
            for domId in self._normaliseListParam( params["selectedDomain"] ):
                self._target.freeDomain( dh.getById( domId ) )
        self._redirect( urlHandlers.UHConfModifAC.getURL( self._target ) )


class RHConfSelectManagers( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfSelectManagers

    def _process( self ):
        p = conferences.WPConfSelectManagers( self, self._target )
        return p.display( **self._getRequestParams() )

class RHConfAddManagers( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfAddManagers

    def _process( self ):
        params = self._getRequestParams()
        if "selectedPrincipals" in params and not "cancel" in params:
            ph = user.PrincipalHolder()
            for id in self._normaliseListParam( params["selectedPrincipals"] ):
                p = ph.getById( id )
                if p:
                    self._target.grantModification( p )
        self._redirect( urlHandlers.UHConfModifAC.getURL( self._target ) )

class RHConfRemoveManagers( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfRemoveManagers

    def _process( self ):
        params = self._getRequestParams()
        if ("selectedPrincipals" in params) and \
            (len(params["selectedPrincipals"])!=0):
            ph = user.PrincipalHolder()
            for id in self._normaliseListParam( params["selectedPrincipals"] ):
                av = ph.getById(id)
                if av:
                    self._target.revokeModification(av)
                else:
                    self._target.getAccessController().revokeModificationEmail(id)
        self._redirect( urlHandlers.UHConfModifAC.getURL( self._target ) )

class RHConfSelectRegistrars( RHConferenceModifBase ):
    _uh = urlHandlers.Derive(urlHandlers.UHConfModifAC, "selectRegistrars")

    def _process( self ):
        p = conferences.WPConfSelectRegistrars( self, self._target )
        return p.display( **self._getRequestParams() )

class RHConfAddRegistrars( RHConferenceModifBase ):
    _uh = urlHandlers.Derive(urlHandlers.UHConfModifAC, "addRegistrars")

    def _process( self ):
        params = self._getRequestParams()
        if "selectedPrincipals" in params and not "cancel" in params:
            ph = user.PrincipalHolder()
            for id in self._normaliseListParam( params["selectedPrincipals"] ):
                p = ph.getById( id )
                if p:
                    self._target.addToRegistrars( p )
        self._redirect( urlHandlers.UHConfModifAC.getURL( self._target ) )

class RHConfRemoveRegistrars( RHConferenceModifBase ):
    _uh = urlHandlers.Derive(urlHandlers.UHConfModifAC, "removeRegistrars")

    def _process( self ):
        params = self._getRequestParams()
        if ("selectedPrincipals" in params) and \
            (len(params["selectedPrincipals"])!=0):
            ph = user.PrincipalHolder()
            for id in self._normaliseListParam( params["selectedPrincipals"] ):
                av = ph.getById(id)
                if av:
                    self._target.removeFromRegistrars(av)
        self._redirect( urlHandlers.UHConfModifAC.getURL( self._target ) )

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
            conveners = ses.getConvenerList()
            for convener in conveners:
                ses.grantModification(convener,False)
        self._redirect( urlHandlers.UHConfModifAC.getURL( self._target ) )

class RHConfModifTools( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModifTools

    def _process( self ):
        if self._conf.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p.display()
        else:
            wf=self.getWebFactory()
            if wf is not None:
                p = wf.getConfModifTools(self, self._conf)
            else:
                p = conferences.WPConfClone( self, self._target )
            return p.display()

class RHConfModifListings( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModifListings

    def _process( self ):
        if self._conf.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p.display()
        else:
            p = conferences.WPConfModifListings( self, self._target )
            wf=self.getWebFactory()
            if wf is not None:
                p = wf.getConfModifListings(self, self._conf)
            return p.display()

class RHConfDeletion( RHConferenceModifBase ):
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


###########################################################################
# Videoconference related
############################
class RHConfModifBookings(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifBookings

    def _checkProtection(self):
        RHConferenceModifBase._checkProtection(self)
        if not self._conf.hasEnabledSection("videoconference"):
            return
            raise MaKaCError( _("The Videoconference section was disabled by the conference managers."), _("videoconference"))

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._bs = params.get( "Booking_Systems", "")

    def _process( self ):
        if self._conf.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p.display()
        else:
            p = conferences.WPConfModifBookings( self, self._conf, self._bs )
            wf = self.getWebFactory()
            if wf is not None:
                p = wf.getConfModifBookings(self, self._conf, self._bs)
            return p.display()

class RHBookingsVRVS(RHConfModifBookings):
    _uh= urlHandlers.UHBookingsVRVS

    def _process(self):

        if self._conf.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p.display()
        else:
            p = conferences.WPBookingsVRVS(self, self._conf)
            return p.display()

class RHBookingsVRVSPerform(RHConfModifBookings):
    _uh= urlHandlers.UHPerformBookingsVRVS

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams( self, params )
        self._cancel = params.has_key("cancel")

    def _process(self):
        if self._conf.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p.display()
        if not self._cancel:
            params = self._getRequestParams()
            if not hasattr(self,"_data"):
                # do not create the booking if it has already been done (db conflict)
                sd = datetime(int(params['sYear']),int(params['sMonth']),int(params['sDay']),int(params["sHour"]),int(params["sMinute"]))
                ed = datetime(int(params['eYear']),int(params['eMonth']),int(params['eDay']),int(params["eHour"]),int(params["eMinute"]))
                headers={'Content-type': 'application/x-www-form-urlencoded', 'Accept': 'text/plain'}
                conn = httplib.HTTPConnection("www.vrvs.org:80")
                conn.request("POST", "/cgi-perl/automaticBooking?%s::%s::%s::%s::%s::%s::%s::%s::%s" %(\
                params['vrvsLogin'],params['vrvsCommunity'],params['vrvsPasswd'], sd.strftime("%Y-%m-%d_%H:%M"), ed.strftime("%Y-%m-%d_%H:%M"), \
                params['accessPasswd'].strip(),params['title'].replace(" ","_"),params['description'].replace(" ","_"),params['supportEmail']),"",headers)
                response = conn.getresponse()
                if response.status != 200:
                    self._data = [response.status, response.reason]
                    return conferences.WPBookingsVRVSserverError( self, self._conf, self._data ).display()
                else:
                    self._data = response.read().split("::")
            if self._data[0].strip() == "DONE":
                b = booking.VRVSBooking(self._conf)
                params["virtualRoom"] = self._data[1]
                b.setValues(params)
                self._conf.addBooking(b)
                return conferences.WPBookingsVRVSPerformed( self, self._conf, b ).display()
            else:
                return conferences.WPBookingsVRVSserverError( self, self._conf, self._data).display()
        else:
            self._redirect(urlHandlers.UHConfModifBookings.getURL(self._conf))


class RHBookingListModifBase( RHConfModifBookings ):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams(self, params)
        self._booking = self._conf.getBookingById(params.get("bookingId",""))


class RHBookingListModifAction ( RHBookingListModifBase ):

    def _checkParams( self, params ):
        RHBookingListModifBase._checkParams(self, params)
        self._selectedBookings = self._normaliseListParam(params.get("bookings",[]))
        self._delete = params.has_key("deleteBookings")
        self._edit = params.has_key("editBookings")
        self._bookinglist = params.get("bookinglist","").split(',')

    def _process( self ):

        if self._delete:
            if len(self._selectedBookings) > 0:
                wp = conferences.WPBookingsModifDeleteConfirmation(self, self._conf, self._selectedBookings)
                return wp.display()
            else:
                return self._redirect(urlHandlers.UHConfModifBookingList.getURL(self._conf))


class RHBookingListDelete (RHBookingListModifBase):

    def _checkParams( self, params ):
        RHBookingListModifBase._checkParams(self, params)
        self.bks=[]
        self._selectedBookings = self._normaliseListParam(params.get("bookings",[]))
        for bk in self._selectedBookings:
            self.bks.append(self._conf.getBookingById(bk))
        self._cancel=params.has_key("cancel")

    def _process(self):
        if not self._cancel:
            for booking in self.bks:
                deldata = self._conf.removeBooking(booking)
                if deldata[0]==1:
                    return conferences.WPBookingsModifDeleteError(self, self._conf, deldata).display()
                elif timezoneUtils.nowutc() > booking.getStartingDate():
                    deldata[0] = _("Warning")
                    deldata[1] = _("Your videoconference passed or has already started.<br>It cannot be deleted but it was removed from the booking list.</br>")
                    return conferences.WPBookingsModifDeleteSuccess(self, self._conf, deldata).display()
                deldata [1] = (_("Your booking was successfully deleted."))
                return conferences.WPBookingsModifDeleteSuccess(self, self._conf, deldata).display()
        else:
            self._redirect(urlHandlers.UHConfModifBookingList.getURL(self._conf))


class RHBookingDetail(RHBookingListModifBase):
    _uh = urlHandlers.UHBookingDetail

    def _checkParams( self, params ):
        RHBookingListModifBase._checkParams(self, params)

    def _process(self):
        return conferences.WPBookingsDetail(self,self._conf,self._booking).display()


class RHHERMESParticipantCreation (RHConfModifBookings):
    _uh = urlHandlers.UHHERMESParticipantCreation

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._cancel = params.has_key("cancel")

    def _process(self):

        if self._conf.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p.display()
        else:
            self._redirect(urlHandlers.UHBookingsHERMES.getURL(self._conf))

################################
# !End of videoconference related
######################################################################################

class RHConfModifParticipants( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModifParticipants

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._errorMsg = params.get("errorMsg","")

    def _process( self ):
        if self._conf.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p.display()
        else:
            p = conferences.WPConfModifParticipants( self, self._target )
            return p.display(errorMsg=self._errorMsg)


class RHConfModifParticipantsObligatory(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifParticipantsObligatory

    def _process( self ):
        if self._conf.getParticipation().isObligatory() :
            self._conf.getParticipation().setInobligatory(self._getUser())
        else:
            self._conf.getParticipation().setObligatory(self._getUser())
        return self._redirect(RHConfModifParticipants._uh.getURL(self._conf))

class RHConfModifParticipantsDisplay(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifParticipantsDisplay

    def _process( self ):
        if self._conf.getParticipation().displayParticipantList() :
            self._conf.getParticipation().participantListHide()
        else:
            self._conf.getParticipation().participantListDisplay()
        return self._redirect(RHConfModifParticipants._uh.getURL(self._conf))


class RHConfModifParticipantsAddedInfo(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifParticipants

    def _process( self ):
        if self._conf.getParticipation().isAddedInfo() :
            self._conf.getParticipation().setNoAddedInfo(self._getUser())
        else:
            self._conf.getParticipation().setAddedInfo(self._getUser())
        return self._redirect(RHConfModifParticipants._uh.getURL(self._conf))

class RHConfModifParticipantsAllowForApplying(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifParticipantsAllowForApplying

    def _process( self ):
        if self._conf.getParticipation().isAllowedForApplying() :
            self._conf.getParticipation().setNotAllowedForApplying(self._getUser())
        else:
            self._conf.getParticipation().setAllowedForApplying(self._getUser())
        return self._redirect(RHConfModifParticipants._uh.getURL(self._conf))

class RHConfModifParticipantsToggleAutoAccept(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifParticipantsToggleAutoAccept

    def _process( self ):
        participantion = self._conf.getParticipation()
        participantion.setAutoAccept(not participantion.getAutoAccept(), self._getUser())
        return self._redirect(RHConfModifParticipants._uh.getURL(self._conf))

class RHConfModifParticipantsPending(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifParticipantsPending

    def _process( self ):
        p = conferences.WPConfModifParticipantsPending( self, self._target )
        return p.display()


class RHConfModifParticipantsAction(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifParticipantsAction

    def _process( self ):
        errorList = []
        infoList = []
        params = self._getRequestParams()
        action = params.get("participantsAction","")
        selectedList = self._normaliseListParam(self._getRequestParams().get("participants",[]))

        if action == _("Remove participant") :
            for id in selectedList :
                self._conf.getParticipation().removeParticipant(id, self._getUser())
        elif action == _("Mark absence") :
            for id in selectedList :
                participant = self._conf.getParticipation().getParticipantById(id)
                participant.setAbsent()
        elif action == _("Mark present"):
            for id in selectedList :
                participant = self._conf.getParticipation().getParticipantById(id)
                participant.setPresent()
        elif action == _("Ask for excuse") :
            data = self._conf.getParticipation().prepareAskForExcuse(self._getUser(), selectedList)
            if data is not None :
                params["emailto"] = ", ".join(data["toList"])
                params["from"] = data["fromAddr"]
                params["subject"] = data["subject"]
                params["body"] = data["body"]
                params["postURL"] = "postURL"
                params["toDisabled"] = True
                params["fromDisabled"] = True
                p = conferences.WPConfModifParticipantsEMail( self, self._target )
                return p.display(**params)
            else :
                if self._getUser() is None :
                    errorList.append( _("""You have to log in to send a message as a manager of this event"""))
                if len(selectedList) == 0 :
                    errorList.append( _("""No participants have been selected - please indicate to whom
                     the message should be send"""))
                if not self._conf.getParticipation().isObligatory() :
                    errorList.append( _("""You cannot ask for excuse because the attendance to this event
                     is NOT OBLIGATORY"""))
                if self._getUser() is not None and len(selectedList) > 0 and self._conf.getParticipation().isObligatory() :
                    errorList.append( _("""One of the error situations listed below occured :"""))
                    errorList.append( _(""" - None of the selected participants was absent in the event"""))
                    errorList.append( _(""" - None of the selected participants has an email address specified"""))
        elif action == _("Excuse absence") :
            for id in selectedList :
                participant = self._conf.getParticipation().getParticipantById(id)
                if not participant.setStatusExcused() and participant.isPresent() :
                    errorList.append( _("""You cannot excuse absence of %s %s %s - this participant was present
                    in the event""")%(participant.getTitle(), participant.getFirstName(), participant.getFamilyName()))
        elif action == _("Send email to") :
            toList = []
            for id in selectedList :
                participant = self._conf.getParticipation().getParticipantById(id)
                toList.append(participant.getEmail())
            params["emailto"] = ", ".join(toList)
            params["toDisabled"] = True
            params["fromDisabled"] = True
            p = conferences.WPConfModifParticipantsEMail( self, self._target )
            return p.display(**params)
        elif action == _("Export to Excel") :
            toList = []
            if selectedList == []:
                toList = self._conf.getParticipation().getParticipantList()
            else:
                for id in selectedList :
                    participant = self._conf.getParticipation().getParticipantById(id)
                    toList.append(participant)
            filename = "ParticipantsList.csv"
            excel = ParticipantsListToExcel(self._conf,list=toList)
            data = excel.getExcelFile()
            self._req.set_content_length(len(data))
            cfg = Config.getInstance()
            mimetype = cfg.getFileTypeMimeType( "CSV" )
            self._req.content_type = """%s"""%(mimetype)
            self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
            return data
        elif action == _("Inform about adding") :
            selected = []
            for id in selectedList :
                selected.append(self._conf.getParticipation().getParticipantById(id))
            eventManager = self._getUser()
            if eventManager is None :
                errorList.append( _("Information about adding to the event has'n been sent."))
                errorList.append( _("Please note, that only logged in event manager can send this message."))
            elif len(selected) == 0 :
                errorList.append( _("Information about adding to the event has'n been sent."))
                errorList.append( _("No participants has been selected."))
            else :
                for participant in selected :
                    data = self._conf.getParticipation().prepareAddedInfo(participant, eventManager)
                    if data is None :
                        errorList.append( _("The message has'n been sent to %s %s - no email provided")%(participant.getFirstName(), participant.getFamilyName()))
                    else :
                        GenericMailer.sendAndLog(GenericNotification(data),self._conf,"participants",self._getUser())
                        infoList.append( _("The message has been send to  %s %s.")%(participant.getFirstName(), participant.getFamilyName()))
        url = RHConfModifParticipants._uh.getURL(self._conf)
        url.addParam("errorMsg",errorList)
        url.addParam("infoMsg",infoList)
        self._redirect(url)



class RHConfModifParticipantsStatistics(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifParticipantsStatistics

    def _process( self ):
        p = conferences.WPConfModifParticipantsStatistics( self, self._target )
        return p.display()


class RHConfModifParticipantsSelectToAdd(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifParticipantsSelectToAdd

    def _process( self ):
        params = self._getRequestParams()
        params["newButtonAction"] = str(urlHandlers.UHConfModifParticipantsNewToAdd.getURL())
        params["addURL"] = str(urlHandlers.UHConfModifParticipantsAddSelected.getURL())
        p = conferences.WPConfModifParticipantsSelect( self, self._target )
        return p.display(**params)


class RHConfModifParticipantsAddSelected(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifParticipantsAddSelected

    def _process( self ):
        params = {}
        errorList = []
        eventManager = self._getUser()
        selectedList = self._normaliseListParam(self._getRequestParams().get("selectedPrincipals",[]))
        for s in selectedList :
            if s[0:8] == "*author*" :
                auths = self._conf.getAuthorIndex()
                selected = auths.getById(s[9:])[0]
            else :
                ph = user.PrincipalHolder()
                selected = ph.getById(s)

            if isinstance(selected, user.Avatar) :
                participant = Participant(self._conf,selected)
                if not self._conf.getParticipation().addParticipant(participant,eventManager) :
                    if self._conf.getParticipation().alreadyParticipating(participant) != 0 :
                        errorList.append( _("""The participant identified by email '%s'
                        is already in the participants' list""")%participant.getEmail())
            elif isinstance(selected, user.Group) :
                for member in selected.getMemberList() :
                    participant = Participant(self._conf,member)
                    if not self._conf.getParticipation().addParticipant(participant,eventManager) :
                        if self._conf.getParticipation().alreadyParticipating(participant) != 0 :
                            errorList.append( _("""The participant identified by email '%s'
                            is already in the participants' list""")%participant.getEmail())
            else :
                eventManager = self._getUser()
                participant = Participant(self._conference)
                participant.setTitle(selected.getTitle())
                participant.setFirstName(selected.getFirstName())
                participant.setFamilyName(selected.getFamilyName())
                participant.setEmail(selected.getEmail())
                participant.setAddress(selected.getAddress())
                participant.setAffiliation(selected.getAffiliation())
                participant.setTelephone(selected.getTelephone())
                participant.setFax(selected.getFax())

                if not self._conf.getParticipation().addParticipant(participant, eventManager) :
                    if self._conf.getParticipation().alreadyParticipating(participant) != 0 :
                        errorList.append( _("""The participant identified by email '%s'
                        is already in the participants' list""")%participant.getEmail())

        url = RHConfModifParticipants._uh.getURL(self._conf)
        url.addParam("errorMsg", errorList)
        self._redirect(url)


class RHConfModifParticipantsNewToAdd(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifParticipantsNewToAdd

    def _process( self ):
        params = self._getRequestParams()
        params["formAction"] = str(urlHandlers.UHConfModifParticipantsAddNew.getURL(self._conf))
        p = conferences.WPConfModifParticipantsNew( self, self._target )
        return p.display(**params)


class RHConfModifParticipantsAddNew(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifParticipantsAddNew

    def _process( self ):
        params = self._getRequestParams()
        errorList = []
        if params.has_key("ok") :
            eventManager = self._getUser()
            av = None
            if params.get("email","") != "":
                av = user.AvatarHolder().match({"email": params.get("email","").strip()}, exact=1, forceWithoutExtAuth=False)
            if av != None and av != []:
                participant = Participant(self._conf,av[0])
            else:
                participant = Participant(self._conf)
                participant.setTitle(params.get("title",""))
                participant.setFamilyName(params.get("surName",""))
                participant.setFirstName(params.get("name",""))
                participant.setEmail(params.get("email",""))
                participant.setAffiliation(params.get("affiliation",""))
                participant.setAddress(params.get("address",""))
                participant.setTelephone(params.get("phone",""))
                participant.setFax(params.get("fax",""))
            if participant.getEmail() == "":
                errorList.append("Participant has not been added because the email address was missing")
            elif participant.getFamilyName().strip() == "" and participant.getFirstName() =="":
                errorList.append("Participant has not been added because name was missing")
            elif not self._conf.getParticipation().addParticipant(participant, eventManager) :
                if self._conf.getParticipation().alreadyParticipating(participant) != 0 :
                        errorList.append( _("""The participant identified by email '%s'
                        is already in the participants' list""")%participant.getEmail())

        url = RHConfModifParticipants._uh.getURL(self._conf)
        url.addParam("errorMsg", errorList)
        self._redirect(url)


class RHConfModifParticipantsSelectToInvite(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifParticipantsSelectToInvite

    def _process( self ):
        params = self._getRequestParams()
        params["newButtonAction"] = str(urlHandlers.UHConfModifParticipantsNewToInvite.getURL())
        params["addURL"] = str(urlHandlers.UHConfModifParticipantsInviteSelected.getURL())
        p = conferences.WPConfModifParticipantsSelect( self, self._target )
        return p.display(**params)


class RHConfModifParticipantsInviteSelected(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifParticipantsInviteSelected

    def _process( self ):
        params = {}
        errorList = []
        eventManager = self._getUser()
        selectedList = self._normaliseListParam(self._getRequestParams().get("selectedPrincipals",[]))
        for s in selectedList :
            if s[0:8] == "*author*" :
                auths = self._conf.getAuthorIndex()
                selected = auths.getById(s[9:])[0]
            else :
                ph = user.PrincipalHolder()
                selected = ph.getById(s)

            if isinstance(selected, user.Avatar) :
                participant = Participant(self._conf,selected)
                if not self._conf.getParticipation().inviteParticipant(participant, eventManager) :
                    if self._conf.getParticipation().alreadyParticipating(participant) != 0 :
                        errorList.append( _("""The participant identified by email '%s'
                        is already in the participants' list""")%participant.getEmail())
            elif isinstance(selected, user.Group) :
                for member in selected.getMemberList() :
                    participant = Participant(self._conf,member)
                    if not self._conf.getParticipation().inviteParticipant(participant, eventManager) :
                        if self._conf.getParticipation().alreadyParticipating(participant) != 0 :
                            errorList.append( _("""The participant identified by email '%s'
                            is already in the participants' list""")%participant.getEmail())
            else :
                participant = Participant(self._conference)
                participant.setTitle(selected.getTitle())
                participant.setFirstName(selected.getFirstName())
                participant.setFamilyName(selected.getFamilyName())
                participant.setEmail(selected.getEmail())
                participant.setAddress(selected.getAddress())
                participant.setAffiliation(selected.getAffiliation())
                participant.setTelephone(selected.getTelephone())
                participant.setFax(selected.getFax())
                if not self._conf.getParticipation().inviteParticipant(participant, eventManager) :
                    if self._conf.getParticipation().alreadyParticipating(participant) != 0 :
                        errorList.append( _("""The participant identified by email '%s'
                        is already in the participants' list""")%participant.getEmail())

        url = RHConfModifParticipants._uh.getURL(self._conf)
        url.addParam("errorMsg", errorList)
        self._redirect(url)


class RHConfModifParticipantsNewToInvite(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifParticipantsNewToInvite

    def _process( self ):
        params = self._getRequestParams()
        params["formAction"] = str(urlHandlers.UHConfModifParticipantsInviteNew.getURL(self._conf))
        p = conferences.WPConfModifParticipantsNew( self, self._target )
        return p.display(**params)


class RHConfModifParticipantsInviteNew(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifParticipantsInviteNew

    def _process( self ):
        params = self._getRequestParams()
        errorList = []
        if params.has_key("ok") :
            eventManager = self._getUser()
            participant = Participant(self._conf)
            participant.setTitle(params.get("title",""))
            participant.setFamilyName(params.get("surName",""))
            participant.setFirstName(params.get("name",""))
            participant.setEmail(params.get("email",""))
            participant.setAffiliation(params.get("affiliation",""))
            participant.setAddress(params.get("address",""))
            participant.setTelephone(params.get("phone",""))
            participant.setFax(params.get("fax",""))
            if not self._conf.getParticipation().inviteParticipant(participant, eventManager) :
                if self._conf.getParticipation().alreadyParticipating(participant) != 0 :
                        errorList.append( _("""The participant identified by email '%s'
                        is already in the participants' list""")%participant.getEmail())

        url = RHConfModifParticipants._uh.getURL(self._conf)
        url.addParam("errorMsg", errorList)
        self._redirect(url)


class RHConfModifParticipantsEdit(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifParticipantsEdit

    def _process( self ):
        params = self._getRequestParams()
        if params.has_key("ok") :
            participantId = params["participantId"]
            participant = self._conf.getParticipation().getParticipantById(participantId)
            participant.setTitle(params.get("title",""))
            participant.setFamilyName(params.get("surName",""))
            participant.setFirstName(params.get("name",""))
            participant.setEmail(params.get("email",""))
            participant.setAffiliation(params.get("affiliation",""))
            participant.setAddress(params.get("address",""))
            participant.setTelephone(params.get("phone",""))
            participant.setFax(params.get("fax",""))

        p = conferences.WPConfModifParticipants( self, self._target )
        return p.display()


class RHConfModifParticipantsDetails(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifParticipantsDetails

    def _process( self ):
        params = self._getRequestParams()
        participantId = params["participantId"]
        del params["participantId"]
        participant = self._conf.getParticipation().getParticipantById(participantId)
        params["formTitle"] =  _("Participant's details")
        if participant is not None :
            params["titleValue"] = participant.getTitle()
            params["surNameValue"] = participant.getFamilyName()
            params["nameValue"] = participant.getFirstName()
            params["emailValue"] = participant.getEmail()
            params["addressValue"] = participant.getAddress()
            params["affiliationValue"] = participant.getAffiliation()
            params["phoneValue"] = participant.getTelephone()
            params["faxValue"] = participant.getFax()

        formAction = urlHandlers.UHConfModifParticipantsEdit.getURL(self._conf)
        formAction.addParam("participantId",participantId)
        params["formAction"] = str(formAction)

        p = conferences.WPConfModifParticipantsNew( self, self._target )
        return p.display(**params)


class RHConfModifParticipantsPendingAction(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifParticipantsPendingAction

    def _process( self ):
        params = self._getRequestParams()
        action = params.get("pendingAction","")
        notification = params.get("emailNotification","yes")
        selectedList = self._normaliseListParam(self._getRequestParams().get("pending",[]))

        if action == "Accept selected" :
            for key in selectedList :
                pending = self._conf.getParticipation().getPendingParticipantByKey(key)
                self._conf.getParticipation().addParticipant(pending)
        elif action == "Reject selected" :
            if (notification == 'yes'):
                for key in selectedList :
                    pending = self._conf.getParticipation().getPendingParticipantByKey(key)
                    pending.setStatusDeclined(sendMail=True)
            else:
                for key in selectedList :
                    pending = self._conf.getParticipation().getPendingParticipantByKey(key)
                    pending.setStatusDeclined(sendMail=False)

        return self._redirect(RHConfModifParticipantsPending._uh.getURL(self._conf))


class RHConfModifParticipantsPendingDetails(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifParticipantsPendingDetails

    def _process( self ):
        params = self._getRequestParams()
        pendingId = params["pendingId"]
        del params["pendingId"]
        pending = self._conf.getParticipation().getPendingParticipantByKey(pendingId)

        if pending is not None :
            params["titleValue"] = pending.getTitle()
            params["surNameValue"] = pending.getFamilyName()
            params["nameValue"] = pending.getFirstName()
            params["emailValue"] = pending.getEmail()
            params["addressValue"] = pending.getAddress()
            params["affiliationValue"] = pending.getAffiliation()
            params["phoneValue"] = pending.getTelephone()
            params["faxValue"] = pending.getFax()

        formAction = urlHandlers.UHConfModifParticipantsPendingEdit.getURL(self._conf)
        formAction.addParam("pendingId",pendingId)
        params["formAction"] = str(formAction)

        p = conferences.WPConfModifParticipantsNew( self, self._target )
        return p.display(**params)


class RHConfModifParticipantsPendingEdit(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifParticipantsPendingEdit

    def _process( self ):
        params = self._getRequestParams()
        if params.has_key("ok") :
            pendingId = params["pendingId"]
            pending = self._conf.getParticipation().getPendingParticipantByKey(pendingId)
            pending.setTitle(params.get("title",""))
            pending.setFamilyName(params.get("surName",""))
            pending.setFirstName(params.get("name",""))
            pending.setEmail(params.get("email",""))
            pending.setAffiliation(params.get("affiliation",""))
            pending.setAddress(params.get("address",""))
            pending.setTelephone(params.get("phone",""))
            pending.setFax(params.get("fax",""))

        p = conferences.WPConfModifParticipantsPending( self, self._target )
        return p.display()



class RHConfModifParticipantsSendEmail (RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifParticipantsSendEmail

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams( self, params )
        self._data = {}
        toList = params.get("to","")
        toList = toList.split(", ")
        self._data["toList"] = toList
        self._data["ccList"] = self._normaliseListParam(params.get("cc",[]))
        self._data["fromAddr"] = params.get("from","")
        self._data["subject"] = params.get("subject","")
        self._data["body"] = params.get("body","")
        self._send = params.has_key("OK")

    def _process(self):
        if self._send:
            GenericMailer.sendAndLog(GenericNotification(self._data),self._conf,"participants", self._getUser())
        self._redirect(urlHandlers.UHConfModifParticipants.getURL(self._conf))

class RHConfAllParticipants( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfAllSessionsConveners

    def _process(self):
        p = conferences.WPConfAllParticipants( self, self._conf )
        return p.display()


class RHConfModifLog (RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifLog

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams( self, params )

        if params.get("filter",None) is not None :
            if params["filter"] == "Action Log" :
                params["filter"] = "action"
            elif params["filter"] == "Email Log" :
                params["filter"] = "email"
            elif params["filter"] == "Custom Log" :
                params["filter"] = "custom"
            elif params["filter"] == "General Log" :
                params["filter"] = "general"

    def  _process(self):
        params = self._getRequestParams()
        p = conferences.WPConfModifLog( self, self._target )
        return p.display(**params)

class RHConfModifLogItem (RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifLogItem

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams( self, params )

    def  _process(self):
        params = self._getRequestParams()
        p = conferences.WPConfModifLogItem( self, self._target )
        return p.display(**params)


class RHConfModifListings( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModifListings

    def _process( self ):
        if self._conf.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p.display()
        else:
            p = conferences.WPConfModifListings( self, self._target )
            wf=self.getWebFactory()
            if wf is not None:
                p = wf.getConfModifListings(self, self._conf)
            return p.display()

#######################################################################################

class RHConfClone( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfClone

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
            p = conferences.WPSentEmail(self, self._target)
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


class RHConfPerformCloning( RHConferenceModifBase ):
    """
    New version of clone functionality -
    fully replace the old one, based on three different actions,
    adds mechanism of selective cloning of materials and access
    privileges attached to an event
    """
    _uh = urlHandlers.UHConfPerformCloning
    _cloneType = "none"

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._date = datetime.today()
        self._cloneType = params["cloneType"]
        if self._cloneType == "once" :
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

        if self._cancel:
            self._redirect( urlHandlers.UHConfModifTools.getURL( self._conf ) )
        elif self._confirm:
            if self._cloneType == "once" :
                newConf = self._conf.clone( self._date, options )
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
                    self._conf.clone(date,options)
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
                    self._conf.clone(date,options)
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
                        date = datetime(int(date.year),int(date.month)+1, 1, int(date.hour), int(date.minute))
                else:
                    rd = self._getFirstDay(date, int(params["day"])) + timedelta((int(params["order"])-1)*7)
                    if rd < date:
                        date = datetime(int(date.year),int(date.month)+1, 1, int(date.hour), int(date.minute))
            while date <= endDate:
                if params["day"] == "OpenDay":
                    od=self._getOpenDay(date,params["order"])
                    if od <= endDate:
                        if confirmed:
                            self._conf.clone(od, options)
                        nbClones += 1
                else:
                    if params["order"] == "last":
                        if self._getLastDay(date,int(params["day"])) <= endDate:
                            if confirmed:
                                self._conf.clone(self._getLastDay(date,int(params["day"])), options)
                            nbClones += 1
                    else:
                        if self._getFirstDay(date, int(params["day"])) + timedelta((int(params["order"])-1)*7) <= endDate:
                            if confirmed:
                                self._conf.clone(self._getFirstDay(date, int(params["day"]))+ timedelta((int(params["order"])-1)*7), options)
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
                        date = datetime(int(date.year),int(date.month)+1, 1, int(date.hour), int(date.minute))
                else:
                    rd = self._getFirstDay(date, int(params["day"])) + timedelta((int(params["order"])-1)*7)
                    if rd < date:
                        date = datetime(int(date.year),int(date.month)+1, 1, int(date.hour), int(date.minute))

            i=0
            stop = int(params["numd"])
            while i < stop:
                i = i + 1
                if params["day"] == "OpenDay":
                    if confirmed:
                        self._conf.clone(self._getOpenDay(date, params["order"]), options)
                    nbClones += 1
                else:
                    if params["order"] == "last":
                        if confirmed:
                            self._conf.clone(self._getLastDay(date,int(params["day"])), options)
                        nbClones += 1
                    else:
                        if confirmed:
                            self._conf.clone(self._getFirstDay(date, int(params["day"]))+ timedelta((int(params["order"])-1)*7), options)
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

        wf=self.getWebFactory()
        if wf is not None:
            p = wf.getConfAddAlarm(self, self._conf)
        else :
            p = conferences.WPConfAddAlarm( self, self._conf )
        return p.display()

class RHCreateAlarm( RHConferenceModifBase ):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        if not params.has_key("fromAddr") or params.get("fromAddr","")=="":
            raise FormValuesError( _("""Please choose a "FROM" address for this alarm"""))
        self._fromAddr=params.get("fromAddr")

    def _process(self):
        params = self._getRequestParams()

        if self._emails:
            if self._alarmId:
                al = self._conf.getAlarmById(self._alarmId)
            else:
                al = self._conf.newAlarm()
            al.initialiseToAddr()
            for addr in self._emails.split(","):
                al.addToAddr(addr.strip())
            al.setFromAddr(self._fromAddr)
            al.setSubject("Event reminder: %s"%self._target.getTitle())
            try:
                locationText = self._target.getLocation().getName()
                if self._target.getLocation().getAddress() != "":
                    locationText += ", %s" % self._target.getLocation().getAddress()
                if self._target.getRoom().getName() != "":
                    locationText += " (%s)" % self._target.getRoom().getName()
            except:
                locationText = ""
            if locationText != "":
                locationText = _(""" _("Location"): %s""") % locationText
            fullName="%s"%self._conf.getTitle()
            if self._getUser() is not None:
                fullName = ",\n%s" % self._getUser().getStraightFullName()
            else:
                fullName = ""
            if Config.getInstance().getShortEventURL() != "":
                url = "%s%s" % (Config.getInstance().getShortEventURL(),self._target.getId())
            else:
                url = urlHandlers.UHConferenceDisplay.getURL( self._target )
            al.setText( _("""Hello,

    Please note that the event "%s" will begin on %s (%s).
    %s

    You can access the full event here:
    %s

Best Regards%s

    """)%(self._target.getTitle(),\
                self._target.getAdjustedStartDate().strftime("%A %d %b %Y at %H:%M"),\
                self._target.getTimezone(),\
                locationText,\
                url,\
                fullName,\
                ))
            al.setNote(self._note)
            if self._includeConf:
                if self._includeConf == "1":
                    al.setConfSumary(True)
                else:
                    al.setConfSumary(False)
            else:
                al.setConfSumary(False)
            self._al = al
        else:
            self._al = None


class RHConfSendAlarm( RHCreateAlarm ):

    def _checkParams( self, params ):
        RHCreateAlarm._checkParams( self, params )
        self._note = params["note"]
        if "includeConf" in params.keys():
            self._includeConf = params["includeConf"]
        else:
            self._includeConf = None
        if "alarmId" in params.keys():
            self._alarmId = params["alarmId"]
        else:
            self._alarmId = None
        if self._aw.getUser():
            self._emails = self._aw.getUser().getEmail()
        else:
            self._emails = None

    def _process( self ):
        RHCreateAlarm._process(self)
        params = self._getRequestParams()

        if self._al:
            self._al.mail.run()
            if not self._alarmId:
                self._conf.removeAlarm(self._al)

        if self._al :
            if params.get("toAllParticipants", False):
                self._al.setToAllParticipants(True)
            else :
                self._al.setToAllParticipants(False)

        self._redirect( urlHandlers.UHConfDisplayAlarm.getURL( self._target ) )

class RHConfSendAlarmNow( RHConfSendAlarm ):

    def _checkParams( self, params ):
        RHCreateAlarm._checkParams( self, params )
        self._note = params["note"]
        if "includeConf" in params.keys():
            self._includeConf = params["includeConf"]
        else:
            self._includeConf = None
        if "alarmId" in params.keys():
            self._alarmId = params["alarmId"]
        else:
            self._alarmId = None

        self._emails = params.get("Emails","")

        emails = []
        if self._emails != "" :
            emails.append(self._emails)
        if params.get("toAllParticipants",None) is not None :
            for p in self._conf.getParticipation().getParticipantList() :
                emails.append(p.getEmail())
            self._emails = ", ".join(emails)

class ConfSendTestAlarm(RHConfSendAlarm):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        if not params.has_key("fromAddr") or params.get("fromAddr","")=="":
            raise FormValuesError( _("""Please choose a "FROM" address for this alarm"""))
        self._fromAddr=params.get("fromAddr")

        self._note = params["note"]
        if "includeConf" in params.keys():
            self._includeConf = params["includeConf"]
        else:
            self._includeConf = None
        self._alarmId = None
        if self._aw.getUser():
            self._emails = self._aw.getUser().getEmail()
        else:
            self._emails = None

class RHConfSaveAlarm( RHCreateAlarm ):

    def _createAlarm(self):
        if self._alarmId:
            al = self._conf.getAlarmById(self._alarmId)
        else:
            al = self._conf.newAlarm()
        al.initialiseToAddr()
        for addr in self._emails.split(","):
            al.addToAddr(addr.strip())
        al.setFromAddr(self._fromAddr)
        al.setSubject("Event reminder: %s"%self._target.getTitle())
        try:
            locationText = self._target.getLocation().getName()
            if self._target.getLocation().getAddress() != "":
                locationText += ", %s" % self._target.getLocation().getAddress()
            if self._target.getRoom().getName() != "":
                locationText += " (%s)" % self._target.getRoom().getName()
        except:
            locationText = ""
        if locationText != "":
            locationText = _(""" _("Location"): %s""") % locationText
        fullName="%s"%self._conf.getTitle()
        if self._getUser() is not None:
            fullName = ",\n%s" % self._getUser().getStraightFullName()
        else:
            fullName = ""
        if Config.getInstance().getShortEventURL() != "":
            url = "%s%s" % (Config.getInstance().getShortEventURL(),self._target.getId())
        else:
            url = urlHandlers.UHConferenceDisplay.getURL( self._target )
        al.setText( _("""Hello,
    Please note that the event "%s" will begin on %s (%s).
    %s

    You can access the full event here:
    %s

Best Regards%s

    """)%(self._target.getTitle(),\
                self._target.getAdjustedStartDate().strftime("%A %d %b %Y at %H:%M"),\
                self._target.getTimezone(),\
                locationText,\
                url,\
                fullName,\
                ))
        al.setNote(self._note)
        if self._includeConf:
            if self._includeConf == "1":
                al.setConfSumary(True)
            else:
                al.setConfSumary(False)
        else:
            al.setConfSumary(False)
        self._al = al

    def _checkParams( self, params ):
        RHCreateAlarm._checkParams( self, params )

        self._dateType = params["dateType"]
        self._year = int(params["year"])
        self._month = int(params["month"])
        self._day = int(params["day"])
        self._hour = int(params["hour"])
        self._dayBefore = params["dayBefore"]
        self._hourBefore = params["hourBefore"]
        self._emails = params.get("Emails","")

        emails = []
        if self._emails != "" :
            emails.append(self._emails)
        self._note = params["note"]
        if "includeConf" in params.keys():
            self._includeConf = params["includeConf"]
        else:
            self._includeConf = None
        if "alarmId" in params.keys():
            self._alarmId = params["alarmId"]
        else:
            self._alarmId = None

    def _process(self):
        RHCreateAlarm._process(self)
        params = self._getRequestParams()

        if not self._al :
            self._createAlarm()

        if params.get("toAllParticipants", False):
            self._al.setToAllParticipants(True)
        else :
            self._al.setToAllParticipants(False)

        if self._dateType == "2":
            self._al.setTimeBefore(timedelta(days=int(self._dayBefore)))
        elif self._dateType == "3":
            self._al.setTimeBefore(timedelta(0, int(self._hourBefore)*3600))
        else:
            self._al.setStartDate(timezone(self._conf.getTimezone()).localize(datetime(self._year, self._month, self._day, self._hour)).astimezone(timezone('UTC')))
        self._redirect( urlHandlers.UHConfDisplayAlarm.getURL( self._target ) )


class RHConfdeleteAlarm( RHAlarmBase ):

    def _process(self):
        self._conf.removeAlarm(self._alarm)
        self._redirect( urlHandlers.UHConfDisplayAlarm.getURL( self._conf ) )


class RHConfModifyAlarm( RHAlarmBase ):

    def _process(self):
        return conferences.WPConfModifyAlarm( self, self._conf, self._alarm ).display()


class RHConfModifProgram( RHConferenceModifBase ):

    def _process( self ):
        p = conferences.WPConfModifProgram( self, self._target )
        return p.display()


class RHProgramDescription( RHConferenceModifBase ):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._cancel = params.has_key("Cancel")
        self._save = params.has_key("Save")
        self._description = params.get("description", "")

    def _process( self ):
        if self._save:
            self._target.setProgramDescription(self._description)
            self._redirect(urlHandlers.UHConfModifProgram.getURL(self._target))
        elif self._cancel:
            self._redirect(urlHandlers.UHConfModifProgram.getURL(self._target))
        else:
            p = conferences.WPConfModifProgramDescription( self, self._target )
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
            websession = self._getSession()
            dict = websession.getVar("ContributionFilterConf%s"%self._conf.getId())
            if not dict:
                    #Create a new dictionary
                    dict = {}
            if dict.has_key('tracks'):
                    #Append the new type to the existing list
                    newDict = dict['tracks'][:]
                    newDict.append(t.getId())
                    dict['tracks'] = newDict[:]
            else:
                    #Create a new entry for the dictionary containing the new type
                    dict['tracks'] = [t.getId()]
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
        self._target.moveUpTrack(self._track)
        self._redirect(urlHandlers.UHConfModifProgram.getURL(self._conf))


class RHProgramTrackDown(RHConferenceModifBase):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._track=self._target.getTrackById(params.get("trackId",""))

    def _process( self ):
        self._target.moveDownTrack(self._track)
        self._redirect(urlHandlers.UHConfModifProgram.getURL(self._conf))

class CFAEnabled(object):
    @staticmethod
    def checkEnabled(request):
        """ Returns true if call for abstracts has been enabled
            Otherwise, throws an exception
        """
        if request._conf.hasEnabledSection("cfa"):
            return True
        else:
            raise MaKaCError( _("You cannot access this option because \"Call for abstracts\" was disabled"))

class RHConfModifCFABase(RHConferenceModifBase):

    def _checkProtection(self):
        from MaKaC.webinterface.rh.reviewingModif import RCAbstractManager
        if not RCAbstractManager.hasRights(self):
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

class RHCFANotifTplNew(RHConfModifCFABase):

    def _checkParams( self, params):
        RHConfModifCFABase._checkParams( self, params)
        self._title=params.get("title", "")
        self._description=params.get("description","")
        self._subject=params.get("subject","")
        self._body=params.get("body","")
        self._fromAddr=params.get("fromAddr","")
        self._toList=self._normaliseListParam(params.get("toAddrs",[]))
        self._ccList=params.get("CCAddrs","").split(",")
        self._cancel=params.get("cancel", None)
        self._save=params.get("save", None)
        self._tplCondition = params.get("condType", None)

    def _process(self):
        error = []
        if self._cancel:
            self._redirect(urlHandlers.UHConfModifCFA.getURL( self._conf ) )
            return
        elif self._save:
            if len(self._toList)<=0:
                error.append( _("""At least one "To Address" must be selected"""))
            elif self._tplCondition is None:
                #TODO: translate
                error.append( _("Choose a condition"))
            else:
                tpl=review.NotificationTemplate()
                tpl.setName(self._title)
                tpl.setDescription(self._description)
                tpl.setTplSubject(self._subject)
                tpl.setTplBody(self._body)
                tpl.setFromAddr(self._fromAddr)
                tpl.setCCAddrList(self._ccList)
                for toAddr in self._toList:
                    toAddrWrapper=conferences.NotifTplToAddrsFactory.getToAddrById(toAddr)
                    if toAddrWrapper:
                        toAddrWrapper.addToAddr(tpl)
                self._conf.getAbstractMgr().addNotificationTpl(tpl)
                url = urlHandlers.UHConfModNotifTplConditionNew.getURL(tpl)
                url.addParams({"condType":self._tplCondition})
                self._redirect(url)
                return
        p=conferences.WPModCFANotifTplNew(self,self._target)
        return p.display(title=self._title,\
                        description=self._description,\
                        subject=self._subject,\
                        body=self._body,\
                        fromAddr=self._fromAddr,\
                        toList=self._toList,\
                        ccList=self._ccList,\
                        errorList=error)


class RHCFANotifTplRem(RHConfModifCFABase):

    def _checkParams( self, params):
        RHConfModifCFABase._checkParams( self, params)
        self._tplIds = self._normaliseListParam( params.get( "selTpls", [] ) )

    def _process(self):
        absMgr = self._conf.getAbstractMgr()
        for id in self._tplIds:
            tpl = absMgr.getNotificationTplById(id)
            absMgr.removeNotificationTpl(tpl)
        self._redirect(urlHandlers.UHConfModifCFA.getURL( self._conf ) )


class RHNotificationTemplateModifBase(RHConfModifCFABase):

    def _checkParams( self, params):
        RHConfModifCFABase._checkParams( self, params)
        l = WebLocator()
        l.setNotificationTemplate(params)
        self._notifTpl = self._target = l.getObject()


class RHCFANotifTplUp(RHNotificationTemplateModifBase):

    def _process(self):
        self._conf.getAbstractMgr().moveUpNotifTpl(self._target)
        self._redirect(urlHandlers.UHConfModifCFA.getURL(self._conf))


class RHCFANotifTplDown(RHNotificationTemplateModifBase):

    def _process(self):
        self._conf.getAbstractMgr().moveDownNotifTpl(self._target)
        self._redirect(urlHandlers.UHConfModifCFA.getURL(self._conf))


class RHCFANotifTplDisplay(RHNotificationTemplateModifBase):

    def _process(self):
        p = conferences.WPModCFANotifTplDisplay(self, self._target)
        return p.display()


class RHCFANotifTplPreview(RHNotificationTemplateModifBase):

    def _process(self):
        p = conferences.WPModCFANotifTplPreview(self, self._target)
        return p.display()


class RHCFANotifTplEdit(RHNotificationTemplateModifBase):

    def _checkParams( self, params):
        RHNotificationTemplateModifBase._checkParams(self, params)
        self._cancel=params.get("cancel", None)
        self._save=params.get("save", None)
        if self._save is not None:
            self._title=params.get("title", "")
            self._description=params.get("description","")
            self._subject=params.get("subject","")
            self._body=params.get("body","")
            self._fromAddr=params.get("fromAddr","")
            self._toList=self._normaliseListParam(params.get("toAddrs",[]))
            self._ccList=params.get("CCAddrs","").split(",")

    def _process(self):
        error=[]
        if self._cancel:
            self._redirect(urlHandlers.UHAbstractModNotifTplDisplay.getURL(self._target))
            return
        elif self._save:
            if len(self._toList)<=0:
                error.append( _("""At least one "To Address" must be seleted """))
                p=conferences.WPModCFANotifTplEdit(self, self._target)
                return p.display(errorList=error, \
                                    title=self._title, \
                                    subject=self._subject, \
                                    body=self._body, \
                                    fromAddr=self._fromAddr, \
                                    toList=self._toList, \
                                    ccList=self._ccList)
            else:
                self._notifTpl.setName(self._title)
                self._notifTpl.setDescription(self._description)
                self._notifTpl.setTplSubject(self._subject)
                self._notifTpl.setTplBody(self._body)
                self._notifTpl.setFromAddr(self._fromAddr)
                self._notifTpl.setCCAddrList(self._ccList)
                self._notifTpl.clearToAddrs()
                for toAddr in self._toList:
                    toAddrWrapper=conferences.NotifTplToAddrsFactory.getToAddrById(toAddr)
                    if toAddrWrapper:
                        toAddrWrapper.addToAddr(self._notifTpl)
                self._redirect(urlHandlers.UHAbstractModNotifTplDisplay.getURL(self._target))
                return
        else:
            p=conferences.WPModCFANotifTplEdit(self, self._target)
            return p.display()


class RHNotifTplConditionNew(RHNotificationTemplateModifBase):

    def _checkParams(self,params):
        RHNotificationTemplateModifBase._checkParams(self,params)
        self._action="OK"
        if params.has_key("CANCEL"):
            self._action="CANCEL"
        self._condType=params.get("condType","")
        cTypeId=params.get("contribType","")
        if cTypeId in ("--none--","--any--"):
            cType=cTypeId
        else:
            abstract=self._target.getOwner()
            cType=abstract.getConference().getContribTypeById(cTypeId)
            if cType is None:
                cType=""
        track=params.get("track","--any--")
        if track not in ["--any--","--none--"]:
            track=self._target.getConference().getTrackById(track)
        self._otherData={"contribType":cType,"track":track}

    def _process(self):
        if self._action=="OK":
            condWrapper=conferences.NotifTplConditionsFactory.getConditionById(self._condType)
            if condWrapper:
                if condWrapper.needsDialog(**self._otherData):
                    pKlass=condWrapper.getDialogKlass()
                    p=pKlass(self,self._target)
                    return p.display()
                else:
                    condWrapper.addCondition(self._target,**self._otherData)
        self._redirect(urlHandlers.UHAbstractModNotifTplDisplay.getURL(self._target))


class RHNotifTplConditionRem(RHNotificationTemplateModifBase):

    def _checkParams(self,params):
        RHNotificationTemplateModifBase._checkParams(self,params)
        self._conds=[]
        for id in self._normaliseListParam(params.get("selCond",[])):
            cond=self._target.getConditionById(id)
            if cond:
                self._conds.append(cond)

    def _process(self):
        for cond in self._conds:
            self._target.removeCondition(cond)
        self._redirect(urlHandlers.UHAbstractModNotifTplDisplay.getURL(self._target))


class RHConfModifCFASelectSubmitter(RHConfModifCFABase):

    def _process( self ):
        p = conferences.WPConfModifCFASelectSubmitters( self, self._target )
        return p.display( **self._getRequestParams() )


class RHConfModifCFAAddSubmitter(RHConfModifCFABase):

    def _process( self ):
        params = self._getRequestParams()
        if "selectedPrincipals" in params and not "cancel" in params:
            ph = user.PrincipalHolder()
            for id in self._normaliseListParam( params["selectedPrincipals"] ):
                if id:
                    self._target.getAbstractMgr().addAuthorizedSubmitter( ph.getById( id ) )
        self._redirect( urlHandlers.UHConfModifCFA.getURL( self._target ) )


class RHConfModifCFARemoveSubmitter(RHConfModifCFABase):

    def _process( self ):
        params = self._getRequestParams()
        if ("selectedPrincipals" in params) and \
            (len(params["selectedPrincipals"])!=0):
            ph = user.PrincipalHolder()
            for id in self._normaliseListParam( params["selectedPrincipals"] ):
                self._target.getAbstractMgr().removeAuthorizedSubmitter( ph.getById( id ) )
        self._redirect( urlHandlers.UHConfModifCFA.getURL( self._target ) )


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

class RHCFAAddType( RHConfModifCFABase ):

    def _checkParams( self, params ):
        RHConfModifCFABase._checkParams( self, params )
        self.type = params["type"]


    def _process( self ):
        self._conf.getAbstractMgr().addContribType(self.type)
        self._redirect( urlHandlers.UHConfModifCFA.getURL( self._conf ) )


class RHCFARemoveType( RHConfModifCFABase ):

    def _checkParams( self, params ):
        RHConfModifCFABase._checkParams( self, params )
        self._types = self._normaliseListParam( params.get( "types", [] ) )


    def _process( self ):
        for type in self._types:
            self._conf.getAbstractMgr().removeContribType(type)
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

            abMgr.setStartSubmissionDate( datetime( int( params["sYear"] ), \
                                        int( params["sMonth"] ), \
                                        int( params["sDay"] ) ))
            abMgr.setEndSubmissionDate( datetime( int( params["eYear"] ), \
                                        int( params["eMonth"] ), \
                                        int( params["eDay"] ) ))
            try:
                sDate = datetime( int( params["sYear"] ), \
                                        int( params["sMonth"] ), \
                                        int( params["sDay"] ) )
            except ValueError,e:
                raise FormValuesError("The start date you have entered is not correct: %s"%e, "Call for Abstracts")
            try:
                eDate = datetime( int( params["eYear"] ), \
                                        int( params["eMonth"] ), \
                                        int( params["eDay"] ) )
            except ValueError,e:
                raise FormValuesError("The end date you have entered is not correct: %s"%e, "Call for Abstracts")
            if eDate < sDate :
                raise FormValuesError("End date can't be before start date!", "Call for Abstracts")
            try:
                mDate = None
                if params["mYear"] or params["mMonth"] or params["mDay"]:
                    mDate = datetime( int( params["mYear"] ), \
                                  int( params["mMonth"] ), \
                                  int( params["mDay"] ) )
            except ValueError,e:
                raise FormValuesError("The modification end date you have entered is not correct: %s"%e, "Call for Abstracts")
            if mDate is not None and (mDate < sDate or mDate < eDate):
                raise FormValuesError("End date must be after end date!", "Call for Abstracts")

            abMgr.setAnnouncement(params["announcement"])
            abMgr.setModificationDeadline( self._modifDL )
            abMgr.getSubmissionNotification().setToList( utils.getEmailList(params.get("toList", "")) )
            abMgr.getSubmissionNotification().setCCList( utils.getEmailList(params.get("ccList", "")) )
            self._redirect( urlHandlers.UHConfModifCFA.getURL( self._conf ) )


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


class AbstractSortingCriteria( filters.SortingCriteria ):
    """
    """
    _availableFields = {
        abstractFilters.ContribTypeSortingField.getId(): \
                                abstractFilters.ContribTypeSortingField, \
        _AbstractStatusSF.getId(): _AbstractStatusSF, \
        _AbstractIdSF.getId(): _AbstractIdSF, \
        abstractFilters.SubmissionDateSortingField.getId() : \
                                    abstractFilters.SubmissionDateSortingField }

class RHAbstractListMenuClose(RHConfModifCFABase):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._currentURL = params.get("currentURL","")

    def _process( self ):
        websession = self._getSession()
        websession.setVar("AbstractListMenuStatus", "close")
        self._redirect(self._currentURL)


class RHAbstractListMenuOpen(RHConfModifCFABase):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._currentURL = params.get("currentURL","")

    def _process( self ):
        websession = self._getSession()
        websession.setVar("AbstractListMenuStatus", "open")
        self._redirect(self._currentURL)


class RHAbstractList(RHConfModifCFABase):
    _uh = urlHandlers.UHConfAbstractManagment

    def _resetFilters( self, sessionData ):
        """
        Brings the filter data to a consistent state (websession),
        marking everything as "checked"
        """

        sessionData["track"] = sessionData["acc_track"] = map(lambda track: track.getId(), self._conf.getTrackList())
        sessionData["type"] = sessionData["acc_type"] = map(lambda contribType: contribType, self._conf.getContribTypeList())
        abstractStatusList = AbstractStatusList.getInstance()
        sessionData["status"] = map(lambda status: abstractStatusList.getId( status ), abstractStatusList.getStatusList())
        sessionData['authSearch'] = ""

        sessionData["trackShowNoValue"] = True
        sessionData["typeShowNoValue"] = True
        sessionData["accTypeShowNoValue"] = True
        sessionData["accTrackShowNoValue"] = True
        sessionData["trackShowMultiple"] = False
        if sessionData.has_key("comment"):
            del sessionData["comment"]

        # TODO: improve this part and do it as with the registrants
        self._fields = {"ID": [ _("ID"), "checked"],
                            "PrimaryAuthor": [ _("Primary Author"), "checked"],
                            "Tracks": [ _("Tracks"), "checked"],
                            "Type": [ _("Type"), "checked"],
                            "Status": [ _("Status"), "checked"],
                            "AccTrack": [ _("Acc. Track"), "checked"],
                            "AccType": [ _("Acc. Type"), "checked"],
                            "SubmissionDate": [ _("Submission Date"), "checked"]}

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

        # TODO: this should work as for the tracks, NOTE hat this filter is used in many
        # places (ContribTypeFilterField and AccContribTypeFilterField should expect ids
        # instead of objects).
        sessionData["type"] = map(lambda contTypeId: self._conf.getContribTypeById(contTypeId), sessionData["type"])
        sessionData["acc_type"] = map(lambda contTypeId: self._conf.getContribTypeById(contTypeId), sessionData["acc_type"])

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


        # TODO: improve this part and do it as with the registrants
        self._fields["ID"] = [ _("ID"), sessionData.get("showID", "")]
        self._fields["PrimaryAuthor"] = [ _("Primary Author"), sessionData.get("showPrimaryAuthor", "")]
        self._fields["Tracks"] = [ _("Tracks"), sessionData.get("showTracks", "")]
        self._fields["Type"] = [ _("Type"), sessionData.get("showType", "")]
        self._fields["Status"] = [ _("Status"), sessionData.get("showStatus", "")]
        self._fields["AccTrack"] = [ _("showAcc. Track"), sessionData.get("showAccTrack", "")]
        self._fields["AccType"] = [ _("showAcc. Type"), sessionData.get("showAccType", "")]
        self._fields["SubmissionDate"] = [ _("Submission Date"), sessionData.get("showSubmissionDate", "")]

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

        self._fields = {}

        operationType = params.get('operationType')

        # session data
        websession = self._getSession()
        sessionData = websession.getVar("abstractFilterAndSortingConf%s"%self._conf.getId())

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

        if params.has_key("resetFilters"):
            operation =  'resetFilters'
        elif operationType ==  'filter':
            operation =  'setFilters'
        else:
            operation = None

        sessionData = self._checkAction(params, filtersActive, sessionData, operation)

        # Maintain the state abotu filter usage
        sessionData['filtersActive'] = self._filterUsed;

        # Save the web session
        websession.setVar("abstractFilterAndSortingConf%s"%self._conf.getId(), sessionData)

        self._filterCrit = self._buildFilteringCriteria(sessionData)

        self._sortingCrit = AbstractSortingCriteria( [sessionData.get( "sortBy", "number" ).strip()] )

        self._order = sessionData.get("order","down")

        self._msg = sessionData.get("directAbstractMsg","")
        self._authSearch = sessionData.get("authSearch", "")

    def _process( self ):
        p = conferences.WPConfAbstractList(self,self._target, self._msg, self._filterUsed)
        return p.display( filterCrit = self._filterCrit,
                            sortingCrit = self._sortingCrit,
                            authSearch=self._authSearch, order=self._order,
                            fields=self._fields)

class RHAbstractsActions:
    """
    class to select the action to do with the selected abstracts
    """
    def __init__(self, req):
        self._req = req

    def process(self, params):
        if params.has_key("newAbstract"):
            return RHNewAbstract(self._req).process(params)
        elif params.has_key("pdf.x"):
            return RHAbstractsToPDF(self._req).process(params)
        elif params.has_key("excel.x"):
            return RHAbstractsListToExcel(self._req).process(params)
        elif params.has_key("xml.x"):
            return RHAbstractsToXML(self._req).process(params)
        elif params.has_key("auth"):
            return RHAbstractsParticipantList(self._req).process(params)
        elif params.has_key("merge"):
            return RHAbstractsMerge(self._req).process(params)
        elif params.has_key("acceptMultiple"):
            return RHAbstractManagmentAcceptMultiple(self._req).process(params)
        elif params.has_key("rejectMultiple"):
            return RHAbstractManagmentRejectMultiple(self._req).process(params)
        return "no action to do"


class RHAbstractsMerge(RHConfModifCFABase):

    def _checkParams(self,params):
        RHConfModifCFABase._checkParams(self,params)
        self._abstractIds=normaliseListParam(params.get("abstracts",[]))
        self._targetAbsId=params.get("targetAbstract","")
        self._inclAuthors=params.has_key("includeAuthors")
        self._notify=params.has_key("notify")
        self._comments=params.get("comments","")
        self._action=""
        if params.has_key("CANCEL"):
            self._action="CANCEL"
        elif params.has_key("OK"):
            self._action="MERGE"
            self._abstractIds=params.get("selAbstracts","").split(",")
        else:
            self._notify=True

    def _process(self):
        errorList=[]
        if self._action=="CANCEL":
            self._redirect(urlHandlers.UHConfAbstractManagment.getURL(self._target))
            return
        elif self._action=="MERGE":
            absMgr=self._target.getAbstractMgr()
            if len(self._abstractIds)==0:
                errorList.append( _("No ABSTRACT TO BE MERGED has been specified"))
            else:
                self._abstracts=[]
                for id in self._abstractIds:
                    abs=absMgr.getAbstractById(id)
                    if abs is None:
                        errorList.append( _("ABSTRACT TO BE MERGED ID '%s' is not valid")%(id))
                    else:
                        statusKlass=abs.getCurrentStatus().__class__
                        if statusKlass in (review.AbstractStatusAccepted,\
                                            review.AbstractStatusRejected,\
                                            review.AbstractStatusWithdrawn,\
                                            review.AbstractStatusDuplicated,\
                                            review.AbstractStatusMerged):
                            label=AbstractStatusList.getInstance().getCaption(statusKlass)
                            errorList.append( _("ABSTRACT TO BE MERGED %s is in status which does not allow to merge (%s)")%(abs.getId(),label.upper()))
                        self._abstracts.append(abs)
            if self._targetAbsId=="":
                errorList.append( _("Invalid TARGET ABSTRACT ID"))
            else:
                if self._targetAbsId in self._abstractIds:
                   errorList.append( _("TARGET ABSTRACT ID is among the ABSTRACT IDs TO BE MERGED"))
                self._targetAbs=absMgr.getAbstractById(self._targetAbsId)
                if self._targetAbs is None:
                   errorList.append( _("Invalid TARGET ABSTRACT ID"))
                else:
                    statusKlass=self._targetAbs.getCurrentStatus().__class__
                    if statusKlass in (review.AbstractStatusAccepted,\
                                        review.AbstractStatusRejected,\
                                        review.AbstractStatusWithdrawn,\
                                        review.AbstractStatusMerged,\
                                        review.AbstractStatusDuplicated):
                        label=AbstractStatusList.getInstance().getInstance().getCaption(statusKlass)
                        errorList.append( _("TARGET ABSTRACT is in status which does not allow to merge (%s)")%label.upper())
            if len(errorList)==0:
                for abs in self._abstracts:
                    abs.mergeInto(self._getUser(),self._targetAbs,\
                        mergeAuthors=self._inclAuthors,comments=self._comments)
                    if self._notify:
                        abs.notify(EmailNotificator(),self._getUser())
                return self._redirect(urlHandlers.UHAbstractManagment.getURL(self._targetAbs))
        p=conferences.WPModMergeAbstracts(self,self._target)
        return p.display(absIdList=self._abstractIds,\
                            targetAbsId=self._targetAbsId, \
                            inclAuth=self._inclAuthors,\
                            comments=self._comments,\
                            errorMsgList=errorList,\
                            notify=self._notify)

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
        self._notify=params.has_key("notify")

    #checks if notification email template is defined for all selected abstracts
    #returns List of abstracts which doesn't have required template
    def _checkNotificationTemplate(self, status):
        from MaKaC.webinterface.rh.abstractModif import _AbstractWrapper
        abstractsWithMissingTemplate = []
        for abstract in self._abstracts:
            status._setAbstract(abstract)
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
                    improperTemplates = self._checkNotificationTemplate(review.AbstractStatusAccepted(None, None, None, None))
                    if self._notify and not self._warningShown and  improperTemplates != []:
                        raise FormValuesError("""The abstracts with the following IDs can not be automatically
                                                 notified: %s. Therefore, none of your request has been processed;
                                                 go back, uncheck the relevant abstracts and try again."""%(", ".join(map(lambda x:x.getId(),improperTemplates))))
                    cType=self._conf.getContribTypeById(self._typeId)
                    for abstract in self._abstracts:
                        abstract.accept(self._getUser(),self._track,cType,self._comments,self._session)
                        if self._notify:
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
        self._notify=params.has_key("notify")
        self._warningShown=params.has_key("confirm")

    def _process( self ):
        if self._abstracts != []:
            improperAbstracts = self._checkStatus()
            if improperAbstracts == []:
                if self._reject:
                    improperTemplates = self._checkNotificationTemplate(review.AbstractStatusRejected(None, None))
                    if self._notify and not self._warningShown and  improperTemplates != []:
                        raise FormValuesError("""The abstracts with the following IDs can not be automatically
                                                 notified: %s. Therefore, none of your request has been processed;
                                                 go back, uncheck the relevant abstracts and try again."""%(", ".join(map(lambda x:x.getId(),improperTemplates))))
                    for abstract in self._abstracts:
                        abstract.reject(self._getUser(), self._comments)
                        if self._notify:
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

    def _process( self ):
        tz = self._conf.getTimezone()
        filename = "Abstracts.pdf"
        if not self._abstractIds:
            return _("No abstract to print")
        pdf = ConfManagerAbstractsToPDF(self._conf, self._abstractIds,tz=tz)
        data = pdf.getPDFBin()
        self._req.set_content_length(len(data))
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "PDF" )
        self._req.content_type = """%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
        return data


class RHAbstractsToXML(RHConfModifCFABase):

    def _checkParams( self, params ):
        RHConfModifCFABase._checkParams( self, params )
        self._abstractIds = normaliseListParam( params.get("abstracts", []) )
        self._abstracts = []
        abMgr = self._conf.getAbstractMgr()
        for id in self._abstractIds:
            #if abMgr.getAbstractById(id).canView( self._aw ):
            self._abstracts.append(abMgr.getAbstractById(id))

    def _process( self ):
        filename = "Abstracts.xml"

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
                x.writeTag(id, abstract.getField(id))
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

        data = x.getXml()

        self._req.headers_out["Content-Length"] = "%s"%len(data)
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "XML" )
        self._req.content_type = """%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
        return data

#-------------------------------------------------------------------------------------

class RHAbstractsListToExcel(RHConfModifCFABase):

    def _checkParams( self, params ):
        RHConfModifCFABase._checkParams( self, params )
        self._abstracts = normaliseListParam( params.get("abstracts", []) )

    def _process( self ):
        filename = "AbstractList.csv"

        abstractList = []
        for id in self._abstracts :
           abstractList.append(self._conf.getAbstractMgr().getAbstractById(id))

        generator = AbstractListToExcel(self._conf,abstractList)
        data = generator.getExcelFile()

        self._req.headers_out["Content-Length"] = "%s"%len(data)
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "CSV" )
        self._req.content_type = """%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
        return data



#-------------------------------------------------------------------------------------

class RHConfModifDisplay( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModifDisplay

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._linkId = params.get("linkId", "")
        self._formatOption = params.get("formatOption", "")
        self._optionalParams={}
        if params.has_key("modifiedText"):
            self._optionalParams["modifiedText"]=params.has_key("modifiedText")

    def _process( self ):
        p = conferences.WPConfModifDisplay(self, self._target, self._linkId, self._formatOption, optionalParams=self._optionalParams )
        return p.display()

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

class RHConfModifDisplayAddPageFileBrowser( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModifDisplayAddPageFileBrowser

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._params = params

    def _process( self ):
        p = conferences.WPConfModifDisplayImageBrowser(self._target, self._req)
        return p.getHTML()

class RHConfModifDisplayAddPageFile( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModifDisplayAddPageFile

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._params = params

    def _sendResults( self, errorNo, fileURL="", filename="", customMsg="" ):
        html = """
<script type="text/javascript">
window.parent.OnUploadCompleted(%s,"%s","%s", "%s") ;
</script>""" % ( errorNo, fileURL.replace('"','\\"'), filename.replace('"','\\"'), customMsg.replace('"','\\"'))
        return html

    def _getNewTempFile( self ):
        cfg = Config.getInstance()
        tempPath = cfg.getUploadedFilesTempDir()
        tempFileName = tempfile.mkstemp( suffix="Indico.tmp", dir = tempPath )[1]
        return tempFileName

    def _saveFileToTemp( self, fd ):
        fileName = self._getNewTempFile()
        f = open( fileName, "wb" )
        f.write( fd.read() )
        f.close()
        return fileName

    def _process( self ):
        self._req.content_type = "text/html"
        if "NewFile" in self._params and not type(self._params["NewFile"]) is types.StringType:
            newFile = self._params["NewFile"]
            if not hasattr(self, "_filePath"):
                #do not save the file again in case it already exists (db conflicts)
                self._filePath = self._saveFileToTemp( newFile.file )
                self._tempFilesToDelete.append(self._filePath)
            self._fileName = newFile.filename
            f = conference.LocalFile()
            f.setName( newFile.filename )
            f.setDescription( _("This image is used in an internal web page") )
            f.setFileName( self._fileName )
            f.setFilePath( self._filePath )
            materialName = "Internal Page Files"
            mats = self._target.getMaterialList()
            mat = None
            existingFile = None
            for m in mats:
                if m.getTitle() == materialName:
                    mat = m
            if mat == None:
                mat = conference.Material()
                mat.setTitle(materialName)
                self._target.addMaterial( mat )
            for file in mat.getResourceList():
                if file.getFileName() == f.getFileName() and file.getSize() == f.getSize():
                    return self._sendResults(0, str(urlHandlers.UHFileAccess.getURL(file)), file.getFileName())
            mat.addResource(f)
            return self._sendResults(0, str(urlHandlers.UHFileAccess.getURL(f)), f.getFileName())
        else:
            return self._sendResults(202)

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
            #create the link

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


class RHConfModifDisplayModifyData( RHConferenceModifBase ):
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
                link.setCaption(name, True)
        else:
            menu = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getMenu()
            link = menu.getLinkById(self._linkId)
            if isinstance(link, displayMgr.SystemLink):
                p = conferences.WPConfModifDisplayModifySystemData(self, self._target, link )
                return p.display()
        self._redirect(urlHandlers.UHConfModifDisplayMenu.getURL(link))

class RHConfModifFormatTitleBgColor( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModifDisplayUpLink

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._linkId = params.get("linkId", "")
        self._formatOption = params.get("formatOption", "")
        self._colorCode = params.get("colorCode", "")

    def _process( self ):
        format = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getFormat()
        if self._formatOption:
            format.setColorCode(self._formatOption, self._colorCode)
        redirecturl = urlHandlers.UHConfModifDisplayCustomization.getURL(self._conf)
        redirecturl.addParam("formatOption", self._formatOption)
        self._redirect("%s#colors"%redirecturl)


class RHConfModifFormatTitleTextColor( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModifDisplayUpLink

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._linkId = params.get("linkId", "")
        self._formatOption = params.get("formatOption", "")
        self._colorCode = params.get("colorCode", "")

    def _process( self ):
        format = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getFormat()
        if self._formatOption:
            format.setColorCode(self._formatOption, self._colorCode)
        redirecturl = urlHandlers.UHConfModifDisplayCustomization.getURL(self._conf)
        redirecturl.addParam("formatOption", self._formatOption)
        self._redirect("%s#colors"%redirecturl)


class RHConfSaveLogo( RHConferenceModifBase ):

    def _getNewTempFile( self ):
        cfg = Config.getInstance()
        tempPath = cfg.getUploadedFilesTempDir()
        tempFileName = tempfile.mkstemp( suffix="IndicoLogo.tmp", dir = tempPath )[1]
        return tempFileName

    def _saveFileToTemp( self, fd ):
        fileName = self._getNewTempFile()
        f = open( fileName, "wb" )
        f.write( fd.read() )
        f.close()
        return fileName

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        if not hasattr(self,"_filePath"):
            self._filePath = self._saveFileToTemp( params["file"].file )
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

    def _saveFileToTemp( self, fd ):
        fileName = self._getNewTempFile()
        f = open( fileName, "wb" )
        f.write( fd.read() )
        f.close()
        return fileName

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._params = params
        if self._params.has_key("FP"):
            self._filePath = self._params["FP"]
            self._fileName = "TemplateInUse"
        else:
            if not hasattr(self,"_filePath"):
                self._filePath = self._saveFileToTemp( params["file"].file )
                self._tempFilesToDelete.append(self._filePath)
            self._fileName = params["file"].filename

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

class RHConfModifPreviewCSS(RHConferenceModifBase):

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

    def _getNewTempFile( self ):
        cfg = Config.getInstance()
        tempPath = cfg.getUploadedFilesTempDir()
        tempFileName = tempfile.mkstemp( suffix="IndicoPic.tmp", dir = tempPath )[1]
        return tempFileName

    def _saveFileToTemp( self, fd ):
        fileName = self._getNewTempFile()
        f = open( fileName, "wb" )
        f.write( fd.read() )
        f.close()
        return fileName

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._filePath = self._saveFileToTemp( params["file"].file )
        self._tempFilesToDelete.append(self._filePath)
        self._fileName = params["file"].filename
        self._params = params


    def _process( self ):
        f = conference.LocalFile()
        f.setFileName( self._fileName )
        f.setFilePath( self._filePath )
        im = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._conf).getImagesManager()
        pic = im.addPic( f )
        from MaKaC.services.interface.rpc import json
        info={"name": f.getFileName(),
                "id": f.getId(),
                "picURL": str(urlHandlers.UHConferencePic.getURL(pic))}
        return "<html><head></head><body>"+json.encode({'status': "OK", 'info': info})+"</body></html>"

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
            websession = self._getSession()
            dict = websession.getVar("ContributionFilterConf%s"%self._conf.getId())
            if not dict:
                #Create a new dictionary
                dict = {}
            if dict.has_key('types'):
                #Append the new type to the existing list
                newDict = dict['types'][:]
                newDict.append(ct.getId())
                dict['types'] = newDict[:]
            else:
                #Create a new entry for the dictionary containing the new type
                dict['types'] = [ct.getId()]

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


class RHContributionListOpenMenu( RHContributionListBase ):

    def _checkParams( self, params ):
        RHContributionListBase._checkParams( self, params )
        self._currentURL = params.get("currentURL","")

    def _process( self ):
        websession = self._getSession()
        websession.setVar("ContribListMenuStatusConf%s"%self._conf.getId(), "open")
        self._redirect(self._currentURL)


class RHContributionListCloseMenu(RHContributionListBase):

    def _checkParams( self, params ):
        RHContributionListBase._checkParams( self, params )
        self._currentURL = params.get("currentURL","")

    def _process( self ):
        websession = self._getSession()
        websession.setVar("ContribListMenuStatusConf%s"%self._conf.getId(), "close")
        self._redirect(self._currentURL)

class RHContributionList( RHContributionListBase ):
    _uh = urlHandlers.UHConfModifContribList

    def _checkProtection(self):
        from MaKaC.webinterface.rh.reviewingModif import RCPaperReviewManager
        if not RCPaperReviewManager.hasRights(self):
            RHContributionListBase._checkProtection(self)

    def _checkParams( self, params ):
        RHContributionListBase._checkParams( self, params )
        websession = self._getSession()
        dict = websession.getVar("ContributionFilterConf%s"%self._conf.getId())
        noMemory = False
        if not dict:
            noMemory = True
            dict = {}
        else:
            dict = dict.copy()
        dict.update(params)
        if params.has_key("OK"):
            if not params.has_key("typeShowNoValue") and dict.has_key("typeShowNoValue"):
                del dict["typeShowNoValue"]
            if not params.has_key("types") and dict.has_key("types"):
                del dict["types"]
            if not params.has_key("sessionShowNoValue") and dict.has_key("sessionShowNoValue"):
                del dict["sessionShowNoValue"]
            if not params.has_key("sessions") and dict.has_key("sessions"):
                del dict["sessions"]
            if not params.has_key("trackShowNoValue") and dict.has_key("trackShowNoValue"):
                del dict["trackShowNoValue"]
            if not params.has_key("tracks") and dict.has_key("tracks"):
                del dict["tracks"]
            if not params.has_key("status") and dict.has_key("status"):
                del dict["status"]
            if not params.has_key("material") and dict.has_key("material"):
                del dict["material"]
        #sorting
        self._sortingCrit=ContribSortingCrit([dict.get("sortBy","number").strip()])
        self._order = dict.get("order","down")
        #filter
        self._authSearch=dict.get("authSearch","")
        #filterUsed=dict.has_key("OK")
        filterUsed = False
        if not noMemory:
            filterUsed = True
        filter = {}
        ltypes = []
        if not filterUsed:
            for type in self._conf.getContribTypeList():
                ltypes.append(type.getId())
        else:
            for id in dict.get("types",[]):
                ltypes.append(id)
        filter["type"]=utils.normalizeToList(ltypes)
        ltracks = []
        if not filterUsed:
            for track in self._conf.getTrackList():
                ltracks.append( track.getId() )
        filter["track"]=utils.normalizeToList(dict.get("tracks",ltracks))
        lsessions = []
        if not filterUsed:
            for session in self._conf.getSessionList():
                lsessions.append(session.getId())
        filter["session"]=utils.normalizeToList(dict.get("sessions",lsessions))
        lstatus=[]
        if not filterUsed:
            for status in ContribStatusList.getList():
                lstatus.append(ContribStatusList.getId(status))
        filter["status"]=utils.normalizeToList(dict.get("status",lstatus))
        lmaterial=[]
        if not filterUsed:
            paperId=materialFactories.PaperFactory().getId()
            slidesId=materialFactories.SlidesFactory().getId()
            for matId in ["--other--","--none--",paperId,slidesId]:
                lmaterial.append(matId)
        filter["material"]=utils.normalizeToList(dict.get("material",lmaterial))
        self._filterCrit=ContribFilterCrit(self._conf,filter)
        typeShowNoValue,trackShowNoValue,sessionShowNoValue=True,True,True
        if filterUsed:
            typeShowNoValue =  dict.has_key("typeShowNoValue")
            trackShowNoValue =  dict.has_key("trackShowNoValue")
            sessionShowNoValue =  dict.has_key("sessionShowNoValue")
        self._filterCrit.getField("type").setShowNoValue( typeShowNoValue )
        self._filterCrit.getField("track").setShowNoValue( trackShowNoValue )
        self._filterCrit.getField("session").setShowNoValue( sessionShowNoValue )


    def _process( self ):
        p = conferences.WPModifContribList(self, self._target)
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

class RHConfAddContribution( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfAddContribution

    def _checkParams( self, params):
        RHConferenceModifBase._checkParams(self,params)
        self._targetDay=None
        if params.get("targetDay", "").strip()!="":
            td=params.get("targetDay").split("-")
            self._targetDay=datetime(int(td[0]),int(td[1]),int(td[2]))
            self._targetDay=self._conf.getSchedule().calculateDayEndDate(self._targetDay)

    def _process( self ):
        p = conferences.WPConfAddContribution( self, self._target )
        wf=self.getWebFactory()
        if wf is not None:
            p = wf.getConfAddContribution(self, self._conf, self._targetDay )
        return p.display()

class RHConfPerformAddContribution( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfPerformAddContribution

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._type=None
        if params.has_key("type") and params["type"].strip()!="":
            self._type=self._conf.getContribTypeById(params["type"])
        self._cancel = params.has_key("cancel")

    def _process( self ):
        if self._cancel:
            self._redirect( urlHandlers.UHConfModifContribList.getURL( self._conf ) )
        else:
            s = conference.Contribution()
            self._conf.addContribution( s )
            s.setParent(self._conf)
            params = self._getRequestParams()
            if params["locationAction"] == "inherit":
                params["locationName"] = ""
            if params["roomAction"] == "inherit":
                params["roomName"] = ""
            elif params["roomAction"] == "exist":
                params["roomName"] = params["exists"]
            elif params["roomAction"] == "define":
                params["roomName"] = params.get( "bookedRoomName" ) or params["roomName"]
            s.setValues( params )
            s.setType(self._type)
            self._redirect( urlHandlers.UHContributionModification.getURL( s ) )


#-------------------------------------------------------------------------------------

class RHScheduleNewContribution( RoomBookingDBMixin, RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModScheduleNewContrib

    def _checkProtection(self):
        if self._session:
            if self._session.canModify(self.getAW()):
                return
            if self._session.canCoordinate(self.getAW(), "unrestrictedSessionTT"):
                return
        RHConferenceModifBase._checkProtection(self)

    def _checkParams( self, params):
        RHConferenceModifBase._checkParams(self,params)

        #this value will be "contributionList" if we are creating a contribution from the Contribution List page
        #otherwise it will have a different value or "other"
        self._contributionCreatedFrom = params.get("contributionCreatedFrom", "other")

        self._session = None
        if params.get("sessionId", None):
            sessionId = params.get("sessionId")
            if isinstance(sessionId, list):
                sessionId = sessionId[0]
            self._session = self._conf.getSessionById(sessionId)

        self._targetDay=None

        if not self._contributionCreatedFrom == "contributionList":
            #we fill the target day so the page is loaded with a default target day
            #if we have created the contribution from the Contribution List page, by default the target day field will be left blank
            if params.get("targetDay", "").strip()!="":
                td=params.get("targetDay").split("-")
                self._targetDay =datetime(int(td[0]),int(td[1]),int(td[2]))
                self._targetDay =self._conf.getSchedule().calculateDayEndDate(self._targetDay)

        if params.get("targetDay", "").strip()!="" :
            self._removePreservedParams()
            self._removeDefinedList("presenter")
            self._removeDefinedList("author")
            self._removeDefinedList("coauthor")
        if params.get("orginURL",None) is None :
            params["orginURL"] = urlHandlers.UHConfModifContribList.getURL(self._conf)
        if params.get("sessionId",None) is None :
            params["sessionId"] = ""
        if params.get("slotId",None) is None :
            params["slotId"] = ""
        if params["slotId"] != "" and params["sessionId"] != "" :
            slot = self._conf.getSessionById(params["sessionId"]).getSlotById(params["slotId"])
            self._targetDay = slot.getStartDate()
            self._targetDay = slot.getSchedule().calculateDayEndDate(self._targetDay)

        self._evt = None
        #if self._session:
        #    self._evt = self._session
        preservedParams = self._getPreservedParams()
        for key in preservedParams.keys():
            if not key in params.keys() or key in ["slotId", "orginURL"] :
                if key == "slotId" and not preservedParams["slotId"]:
                    continue
                params[key] = preservedParams[key]
        #params.update(preservedParams)
        self._preserveParams( params )


    def _process( self ):
        if not self._session:
            p = conferences.WPModScheduleNewContrib( self, self._target, self._targetDay, self._contributionCreatedFrom)
        else:
            p = sessions.WPModScheduleNewContrib( self, self._session, self._targetDay )
        params = self._getRequestParams()
        params = copy(params)

        params["presenterDefined"] = self._getDefinedList("presenter",True)
        params["authorDefined"] = self._getDefinedList("author",False)
        params["coauthorDefined"] = self._getDefinedList("coauthor",False)
        params["presenterOptions"] = self._getPersonOptions("presenter")
        params["authorOptions"] = self._getPersonOptions("author")
        params["coauthorOptions"] = self._getPersonOptions("coauthor")

        return p.display(**params)

    def _getPreservedParams(self):
        params = self._websession.getVar("preservedParams")
        if params is None :
            return {}
        return params

    def _preserveParams(self, params):
        self._websession.setVar("preservedParams",params)

    def _getDefinedList(self, typeName, submission):
        definedList = self._websession.getVar("%sList"%typeName)
        if definedList is None :
            return []
        return definedList

    def _removeDefinedList(self, typeName):
        self._websession.setVar("%sList"%typeName,None)

    def _removePreservedParams(self):
        self._websession.setVar("preservedParams",None)

    def _personInDefinedList(self, typeName, person):
        list = self._websession.getVar("%sList"%typeName)
        if list is None :
            return False
        for p in list :
            if person.getFullName()+" "+person.getEmail() == p[0].getFullName()+" "+p[0].getEmail() :
                return True
        return False

    def _getPersonOptions(self, typeName):
        html = []
        names = []
        text = {}
        html.append("""<option value=""> </option>""")
        for contribution in self._conf.getContributionList() :
            for speaker in contribution.getSpeakerList() :
                name = speaker.getFullNameNoTitle()
                if not name in names and not self._personInDefinedList(typeName, speaker):
                    text[name] = """<option value="s%s-%s">%s</option>"""%(contribution.getId(),speaker.getId(),name)
                    names.append(name)
            for author in contribution.getAuthorList() :
                name = author.getFullNameNoTitle()
                if not name in names and not self._personInDefinedList(typeName, author):
                    text[name] = """<option value="a%s-%s">%s</option>"""%(contribution.getId(),author.getId(),name)
                    names.append(name)
            for coauthor in contribution.getCoAuthorList() :
                name = coauthor.getFullNameNoTitle()
                if not name in names and not self._personInDefinedList(typeName, coauthor):
                    text[name] = """<option value="c%s-%s">%s</option>"""%(contribution.getId(),coauthor.getId(),name)
                    names.append(name)
        names.sort()
        for name in names:
            html.append(text[name])
        return "".join(html)

#-------------------------------------------------------------------------------------

class RHSchedulePerformNewContribution( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModSchedulePerformNewContrib

    def _checkProtection(self):
        if self._session:
            if self._session.canModify(self.getAW()):
                return
            if self._session.canCoordinate(self.getAW(), "unrestrictedSessionTT"):
                return
        RHConferenceModifBase._checkProtection(self)

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._target = self._conf
        self._session = None

        if params.get("sessionId", None):
            sessionId = params.get("sessionId")
            if isinstance(sessionId, list):
                sessionId = sessionId[0]
                params["sessionId"] = sessionId
            self._session = self._conf.getSessionById(sessionId)
            self._target = self._session

        self._cancel = params.has_key("cancel")

        #self._hasTargetDay will be false only if we created the contribution fron the Contribution List page
        #and if all the fields were left blank
        self._hasTargetDay = not (
                                  params.get("contributionCreatedFrom", "other") == "contributionList" and \
                                  params.get("sYear","").strip()=="" and params.get("sMonth","").strip()=="" and \
                                  params.get("sDay","").strip()=="" and params.get("sHour", "").strip()=="" and \
                                  params.get("sMinute", "").strip()==""
                                  )

        #default value for targetDay: None
        self._targetDay = None

        if self._hasTargetDay:

            if params.get("sYear","").strip()=="" or params.get("sMonth","").strip()=="" or \
                            params.get("sDay","").strip()=="" or params.get("sHour", "").strip()=="" or \
                            params.get("sMinute", "").strip()=="":
                raise MaKaCError("The starting date for the contribution is not complete, please fill all the fields.")

            ########################################
            # Fermi timezone awareness             #
            #  The time received from the form is  #
            #  relative to the conf tz.            #
            ########################################
            tz = self._conf.getTimezone()
            sd = timezone(tz).localize(datetime(int(params["sYear"]), \
                 int(params["sMonth"]),int(params["sDay"]), \
                 int(params["sHour"]),int(params["sMinute"])))
            self._targetDay = sd.astimezone(timezone('UTC'))

            ########################################
            # Fermi timezone awareness(end)        #
            ########################################

        if params.get("durHours", "").strip()=="" or params.get("durMins", "").strip()=="" or \
                (params.get("durHours", "")=="0" and params.get("durMins", "")=="0"):
            params["durHours"]="0"
            params["durMins"]="20"

        preservedParams = self._getPreservedParams()
        for key in preservedParams.keys():
            if not key in params.keys():
                params[key] = preservedParams[key]
        if params.get("ok"):
            if "performedAction" in params.keys():
                del params["performedAction"]
        self._preserveParams()

    def _process( self ):
        params = self._getRequestParams()

        if self._cancel:
            self._removePreservedParams()
            self._removeDefinedList("presenter")
            self._removeDefinedList("author")
            self._removeDefinedList("coauthor")
            self._redirect(params["orginURL"])
        elif params.get("performedAction","") == "Search author" :
            self._preserveParams()
            url = urlHandlers.UHConfModScheduleAuthorSearch.getURL(self._target)
            url.addParam("eventType",params.get("eventType","conference"))
            self._redirect(url)
        elif params.get("performedAction","") == "New author" :
            self._preserveParams()
            url = urlHandlers.UHConfModScheduleAuthorNew.getURL(self._target)
            url.addParam("eventType",params.get("eventType","conference"))
            self._redirect(url)
        elif params.get("performedAction","") == "Search coauthor" :
            self._preserveParams()
            url = urlHandlers.UHConfModScheduleCoauthorSearch.getURL(self._target)
            url.addParam("eventType",params.get("eventType","conference"))
            self._redirect(url)
        elif params.get("performedAction","") == "New coauthor" :
            self._preserveParams()
            url = urlHandlers.UHConfModScheduleCoauthorNew.getURL(self._target)
            url.addParam("eventType",params.get("eventType","conference"))
            self._redirect(url)
        elif params.get("performedAction","") == "Search presenter" :
            self._preserveParams()
            url = urlHandlers.UHConfModSchedulePresenterSearch.getURL(self._target)
            url.addParam("eventType",params.get("eventType","conference"))
            self._redirect(url)
        elif params.get("performedAction","") == "New presenter" :
            self._preserveParams()
            url = urlHandlers.UHConfModSchedulePresenterNew.getURL(self._target)
            url.addParam("eventType",params.get("eventType","conference"))
            self._redirect(url)
        elif params.get("performedAction","") == "Add as author" :
            self._preserveParams()
            url = urlHandlers.UHConfModSchedulePersonAdd.getURL(self._target)
            url.addParam("orgin","added")
            url.addParam("typeName","author")
            self._redirect(url)
        elif params.get("performedAction","") == "Add as coauthor" :
            self._preserveParams()
            url = urlHandlers.UHConfModSchedulePersonAdd.getURL(self._target)
            url.addParam("orgin","added")
            url.addParam("typeName","coauthor")
            self._redirect(url)
        elif params.get("performedAction","") == "Add as presenter" :
            self._preserveParams()
            url = urlHandlers.UHConfModSchedulePersonAdd.getURL(self._target)
            url.addParam("orgin","added")
            url.addParam("typeName","presenter")
            self._redirect(url)
        elif params.get("performedAction","") == "Remove presenters" :
            self._removePersons(params, "presenter")
        elif params.get("performedAction","") == "Remove authors" :
            self._removePersons(params, "author")
        elif params.get("performedAction","") == "Remove coauthors" :
            self._removePersons(params, "coauthor")
        elif params.get("performedAction","") == "Grant submission" :
            self._grantSubmission(params, "presenter")
        elif params.get("performedAction","") == "Withdraw submission" :
            self._withdrawSubmission(params, "presenter")
        else:
            contribution = conference.Contribution()
            if not params.has_key("check"):
                params["check"] = 1
            if params["sessionId"] != "" and params["slotId"] != "" :
                session = self._conf.getSessionById(params["sessionId"])
                slot = session.getSlotById(params["slotId"])
                session.addContribution(contribution)
                contribution.setParent(session.getConference())
                if slot.getSession().getScheduleType() == "poster":
                    contribution.setStartDate(slot.getStartDate(), int(params['check']))
                else:
                    contribution.setStartDate(self._targetDay, params["check"])
                contribution.setDuration(hours=params["durHours"],minutes=params["durMins"])
                #We add the contribution to the schedule only if a start date has been defined
                if self._targetDay:
                    schedule = slot.getSchedule()
                    schedule.addEntry(contribution.getSchEntry(), int(params["check"]))
            else :
                self._conf.addContribution( contribution )
                contribution.setParent(self._conf)
                #########################################
                # Fermi timezone awareness              #
                #   targetDay is naive, relative to the #
                #   conf timezone                       #
                #########################################
                sd = self._targetDay
                contribution.setStartDate(self._targetDay)
                #We add the contribution to the schedule only if a start date has been defined
                if self._targetDay:
                    self._target.getSchedule().addEntry(contribution.getSchEntry(),int(params['check']))
            contribution.setValues( params,int(params["check"]) )
            if params.get("presenterFreeText","") != "":
                presenter = ContributionParticipation()
                presenter.setFamilyName(params.get("presenterFreeText",""))
                contribution.newSpeaker(presenter)
            presenterList = self._getDefinedList("presenter")
            for presenter in presenterList :
                contribution.newSpeaker(presenter[0])
                if presenter[1] :
                    contribution.grantSubmission(presenter[0])
            authorList = self._getDefinedList("author")
            for author in authorList :
                contribution.addPrimaryAuthor(author[0])
                if author[1] :
                    contribution.grantSubmission(author[0])
            coauthorList = self._getDefinedList("coauthor")
            for coauthor in coauthorList :
                contribution.addCoAuthor(coauthor[0])
                if coauthor[1] :
                    contribution.grantSubmission(coauthor[0])
            logInfo = contribution.getLogInfo()
            logInfo["subject"] =  _("Create new contribution: %s")%contribution.getTitle()
            self._conf.getLogHandler().logAction(logInfo,"Timetable/Contribution",self._getUser())

            self._removePreservedParams()
            self._removeDefinedList("presenter")
            self._removeDefinedList("author")
            self._removeDefinedList("coauthor")

            self._redirect(params["orginURL"])

    def _preserveParams(self):
        preservedParams = self._getRequestParams().copy()
        self._websession.setVar("preservedParams",preservedParams)

    def _getPreservedParams(self):
        params = self._websession.getVar("preservedParams")
        if params is None :
            return {}
        return params

    def _removePersons(self, params, typeName):
        persons = self._normaliseListParam(params.get("%ss"%typeName,[]))
        definedList = self._getDefinedList(typeName)
        personsToRemove = []
        for p in persons :
            if int(p) < len(definedList) or int(p) >= 0 :
                personsToRemove.append(definedList[int(p)])
        for person in personsToRemove :
            definedList.remove(person)
        self._setDefinedList(definedList,typeName)
        url = urlHandlers.UHConfModScheduleNewContrib.getURL(self._target)
        url.addParam("eventType",params.get("eventType","conference"))
        self._redirect(url)

    def _grantSubmission(self, params, typeName):
        persons = self._normaliseListParam(params.get("%ss"%typeName,[]))
        definedList = self._getDefinedList(typeName)
#        import sys
#        print >> sys.stderr, str(definedList)
#        print >> sys.stderr, str(persons)
#        sys.stderr.flush()
        for p in persons :
            if int(p) >= 0 and int(p) < len(definedList)  :
                if definedList[int(p)][0].getEmail() != "":
                    definedList[int(p)][1] = True
        self._setDefinedList(definedList,typeName)
        url = urlHandlers.UHConfModScheduleNewContrib.getURL(self._target)
        url.addParam("eventType",params.get("eventType","conference"))
        self._redirect(url)

    def _withdrawSubmission(self, params, typeName):
        persons = self._normaliseListParam(params.get("%ss"%typeName,[]))
        definedList = self._getDefinedList(typeName)
        for p in persons :
            if int(p) >= 0 and int(p) < len(definedList)  :
                definedList[int(p)][1] = False
        self._setDefinedList(definedList,typeName)
        url = urlHandlers.UHConfModScheduleNewContrib.getURL(self._target)
        url.addParam("eventType",params.get("eventType","conference"))
        self._redirect(url)


    def _removePreservedParams(self):
        self._websession.setVar("preservedParams",None)

    def _removeDefinedList(self, typeName):
        self._websession.setVar("%sList"%typeName,None)

    def _getDefinedList(self, typeName):
        definedList = self._websession.getVar("%sList"%typeName)
        if definedList is None :
            return []
        return definedList

    def _setDefinedList(self, definedList, typeName):
        self._websession.setVar("%sList"%typeName,definedList)

#-------------------------------------------------------------------------------------

class RHNewContributionAuthorSearch( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModScheduleAuthorSearch

    def _checkParams( self, params):
        RHConferenceModifBase._checkParams(self,params)
        self._session = None
        if params.get("sessionId", None):
            self._session = self._conf.getSessionById(params.get("sessionId"))
            self._target = self._session

    def _checkProtection(self):
        if self._session:
            if self._session.canModify(self.getAW()):
                return
            if self._session.canCoordinate(self.getAW(), "unrestrictedSessionTT"):
                return
        RHConferenceModifBase._checkProtection(self)

    def _process( self ):
        params = self._getRequestParams()

        params["newButtonAction"] = str(urlHandlers.UHConfModScheduleAuthorNew.getURL())
        addURL = urlHandlers.UHConfModSchedulePersonAdd.getURL()
        addURL.addParam("orgin","selected")
        addURL.addParam("typeName","author")
        params["addURL"] = addURL
        p = conferences.WPNewContributionAuthorSelect( self, self._target)
        return p.display(**params)

#-------------------------------------------------------------------------------------

class RHNewContributionAuthorNew( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModScheduleAuthorNew

    def _checkParams( self, params):
        RHConferenceModifBase._checkParams(self,params)
        self._session = None
        if params.get("sessionId", None):
            self._session = self._conf.getSessionById(params.get("sessionId"))
            self._target = self._session

    def _checkProtection(self):
        if self._session:
            if self._session.canModify(self.getAW()):
                return
            if self._session.canCoordinate(self.getAW(), "unrestrictedSessionTT"):
                return
        RHConferenceModifBase._checkProtection(self)

    def _process( self ):
        p = conferences.WPNewContributionAuthorNew( self, self._target, {})
        return p.display()

#-------------------------------------------------------------------------------------

class RHNewContributionCoauthorSearch( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModScheduleCoauthorSearch

    def _checkParams( self, params):
        RHConferenceModifBase._checkParams(self,params)
        self._session = None
        if params.get("sessionId", None):
            self._session = self._conf.getSessionById(params.get("sessionId"))
            self._target = self._session

    def _checkProtection(self):
        if self._session:
            if self._session.canModify(self.getAW()):
                return
            if self._session.canCoordinate(self.getAW(), "unrestrictedSessionTT"):
                return
        RHConferenceModifBase._checkProtection(self)

    def _process( self ):
        params = self._getRequestParams()

        params["newButtonAction"] = str(urlHandlers.UHConfModScheduleCoauthorNew.getURL())
        addURL = urlHandlers.UHConfModSchedulePersonAdd.getURL()
        addURL.addParam("orgin","selected")
        addURL.addParam("typeName","coauthor")
        params["addURL"] = addURL
        p = conferences.WPNewContributionCoauthorSelect( self, self._target)
        return p.display(**params)

#-------------------------------------------------------------------------------------

class RHNewContributionCoauthorNew( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModScheduleCoauthorNew

    def _checkParams( self, params):
        RHConferenceModifBase._checkParams(self,params)
        self._session = None
        if params.get("sessionId", None):
            self._session = self._conf.getSessionById(params.get("sessionId"))
            self._target = self._session

    def _checkProtection(self):
        if self._session:
            if self._session.canModify(self.getAW()):
                return
            if self._session.canCoordinate(self.getAW(), "unrestrictedSessionTT"):
                return
        RHConferenceModifBase._checkProtection(self)

    def _process( self ):
        p = conferences.WPNewContributionCoauthorNew( self, self._target, {})
        return p.display()
#-------------------------------------------------------------------------------------

class RHNewContributionPresenterSearch( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModSchedulePresenterSearch

    def _checkParams( self, params):
        RHConferenceModifBase._checkParams(self,params)
        self._session = None
        if params.get("sessionId", None):
            self._session = self._conf.getSessionById(params.get("sessionId"))
            self._target = self._session

    def _checkProtection(self):
        if self._session:
            if self._session.canModify(self.getAW()):
                return
            if self._session.canCoordinate(self.getAW(), "unrestrictedSessionTT"):
                return
        RHConferenceModifBase._checkProtection(self)

    def _process( self ):
        params = self._getRequestParams()

        params["newButtonAction"] = str(urlHandlers.UHConfModSchedulePresenterNew.getURL())
        addURL = urlHandlers.UHConfModSchedulePersonAdd.getURL()
        addURL.addParam("orgin","selected")
        addURL.addParam("typeName","presenter")
        params["addURL"] = addURL
        p = conferences.WPNewContributionPresenterSelect( self, self._target)
        return p.display(**params)

#-------------------------------------------------------------------------------------

class RHNewContributionPresenterNew( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModSchedulePresenterNew

    def _checkParams( self, params):
        RHConferenceModifBase._checkParams(self,params)
        self._session = None
        if params.get("sessionId", None):
            self._session = self._conf.getSessionById(params.get("sessionId"))
            self._target = self._session

    def _checkProtection(self):
        if self._session:
            if self._session.canModify(self.getAW()):
                return
            if self._session.canCoordinate(self.getAW(), "unrestrictedSessionTT"):
                return
        RHConferenceModifBase._checkProtection(self)

    def _process( self ):
        p = conferences.WPNewContributionPresenterNew( self, self._target, {})
        return p.display()

#-------------------------------------------------------------------------------------

class RHNewContributionPersonAdd( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModSchedulePersonAdd

    def _checkParams( self, params):
        RHConferenceModifBase._checkParams(self,params)
        self._session = None
        if params.get("sessionId", None):
            self._session = self._conf.getSessionById(params.get("sessionId"))
            self._target = self._session
        self._typeName = params.get("typeName",None)
        if self._typeName  is None :
            raise MaKaCError( _("Type name of the person to add is not set."))

    def _checkProtection(self):
        if self._session:
            if self._session.canModify(self.getAW()):
                return
            if self._session.canCoordinate(self.getAW(), "unrestrictedSessionTT"):
                return
        RHConferenceModifBase._checkProtection(self)


    def _process( self ):
        params = self._getRequestParams()
        self._errorList = []
        definedList = self._getDefinedList(self._typeName)
        if definedList is None :
            definedList = []
        if params.get("orgin","") == "new" :

            if params.get("ok",None) is None:
                self._redirect(urlHandlers.UHConfModScheduleNewContrib.getURL(self._conf))
                return
            else :

                if params["email"]!="" and  not utils.validMail(params["email"]):

                       param={}
                       param["surNameValue"] = str(params["surName"])
                       param["nameValue"] = str(params["name"])
                       param["emailValue"] = str(params["email"])
                       param["titleValue"] = str(params["title"])
                       param["addressValue"] = str(params["address"])

                       param["affiliationValue"] = str(params["affiliation"])

                       param["phoneValue"] = str(params["phone"])

                       param["faxValue"] = str(params["fax"])
                       param["msg"] = "INSERT A VALID E-MAIL ADRESS"
                       if params.has_key("submissionControl"):
                           param["submissionControlValue"]="checked"

                       if params["typeName"]=="author":
                           p=conferences.WPNewContributionAuthorNew(self, self._conf, param)
                       if params["typeName"]=="coauthor":
                           p=conferences.WPNewContributionCoauthorNew(self, self._conf, param)
                       if params["typeName"]=="presenter":
                           p=conferences.WPNewContributionPresenterNew(self, self._conf, param)

                       return p.display()



                person = ContributionParticipation()
                person.setFirstName(params["name"])
                person.setFamilyName(params["surName"])
                person.setEmail(params["email"])



                person.setAffiliation(params["affiliation"])
                person.setAddress(params["address"])
                person.setPhone(params["phone"])
                person.setTitle(params["title"])
                person.setFax(params["fax"])
                if not self._alreadyDefined(person, definedList) :
                    submControl=False
                    if params["email"].strip()!="":
                        submControl=params.has_key("submissionControl")
                    definedList.append([person, submControl])

                else :
                    self._errorList.append( _("%s has been already defined as %s of this contribution")%(person.getFullName(),self._typeName))





        elif params.get("orgin","") == "selected" :
            selectedList = self._normaliseListParam(self._getRequestParams().get("selectedPrincipals",[]))
            for s in selectedList :
                if s[0:8] == "*author*" :
                    auths = self._conf.getAuthorIndex()
                    selected = auths.getById(s[9:])[0]
                else :
                    ph = user.PrincipalHolder()
                    selected = ph.getById(s)
                if isinstance(selected, user.Avatar) :
                    person = ContributionParticipation()
                    person.setDataFromAvatar(selected)
                    if not self._alreadyDefined(person, definedList) :
                        definedList.append([person,params.has_key("submissionControl")])
                    else :
                        self._errorList.append( _("%s has been already defined as %s of this contribution")%(person.getFullName(),self._typeName))

                elif isinstance(selected, user.Group) :
                    for member in selected.getMemberList() :
                        person = ContributionParticipation()
                        person.setDataFromAvatar(member)
                        if not self._alreadyDefined(person, definedList) :
                            definedList.append([person,params.has_key("submissionControl")])
                        else :
                            self._errorList.append( _("%s has been already defined as %s of this contribution")%(presenter.getFullName(),self._typeName))
                else :
                    person = ContributionParticipation()
                    person.setTitle(selected.getTitle())
                    person.setFirstName(selected.getFirstName())
                    person.setFamilyName(selected.getFamilyName())
                    person.setEmail(selected.getEmail())
                    person.setAddress(selected.getAddress())
                    person.setAffiliation(selected.getAffiliation())
                    person.setPhone(selected.getPhone())
                    person.setFax(selected.getFax())
                    if not self._alreadyDefined(person, definedList) :
                        definedList.append([person,params.has_key("submissionControl")])
                    else :
                        self._errorList.append( _("%s has been already defined as %s of this contribution")%(person.getFullName(),self._typeName))

        elif params.get("orgin","") == "added" :
            preservedParams = self._getPreservedParams()
            chosen = preservedParams.get("%sChosen"%self._typeName,None)
            if chosen is None or chosen == "" :
                self._redirect(urlHandlers.UHConfModScheduleNewContrib.getURL(self._target))
                return
            index = chosen.find("-")

            if index == -1:
                ah = user.AvatarHolder()
                chosenPerson = ContributionParticipation()
                chosenPerson.setDataFromAvatar(ah.getById(chosen))
            else:
                contributionId = chosen[1:index]
                chosenId = chosen[index+1:len(chosen)]
                contribution = self._conf.getContributionById(contributionId)
                chosenPerson = None
                if chosen[0:1] == "s" :
                    chosenPerson = contribution.getSpeakerById(chosenId)
                elif chosen[0:1] == "a" :
                    chosenPerson = contribution.getAuthorById(chosenId)
                elif chosen[0:1] == "c" :
                    chosenPerson = contribution.getCoAuthorById(chosenId)

            if chosenPerson is None :
                self._redirect(urlHandlers.UHConfModScheduleNewContrib.getURL(self._target))
                return
            person = ContributionParticipation()
            person.setTitle(chosenPerson.getTitle())
            person.setFirstName(chosenPerson.getFirstName())
            person.setFamilyName(chosenPerson.getFamilyName())
            person.setEmail(chosenPerson.getEmail())
            person.setAddress(chosenPerson.getAddress())
            person.setAffiliation(chosenPerson.getAffiliation())
            person.setPhone(chosenPerson.getPhone())
            person.setFax(chosenPerson.getFax())
            if not self._alreadyDefined(person, definedList) :
                definedList.append([person,params.has_key("submissionControl")])
            else :
                self._errorList.append( _("%s has been already defined as %s of this contribution")%(person.getFullName(),self._typeName))
        else :
            self._redirect(urlHandlers.UHConfModifSchedule.getURL(self._target))
            return
        preservedParams = self._getPreservedParams()
        preservedParams["errorMsg"] = self._errorList
        self._preserveParams(preservedParams)
        self._websession.setVar("%sList"%self._typeName,definedList)

        self._redirect(urlHandlers.UHConfModScheduleNewContrib.getURL(self._target))


    def _getDefinedList(self, typeName):
        definedList = self._websession.getVar("%sList"%typeName)
        if definedList is None :
            return []
        return definedList

    def _alreadyDefined(self, person, definedList):
        if person is None :
            return True
        if definedList is None :
            return False
        fullName = person.getFullName()
        for p in definedList :
            if p[0].getFullName() == fullName :
                return True
        return False

    def _getPreservedParams(self):
        params = self._websession.getVar("preservedParams")
        if params is None :
            return {}
        return params

    def _preserveParams(self, params):
        self._websession.setVar("preservedParams",params)
    def _removePreservedParams(self):
        self._websession.setVar("preservedParams",None)

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
        submitterEmails = Set()
        primaryAuthorEmails = Set()
        coAuthorEmails = Set()

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


class RHNewAbstract(RHConfModifCFABase):

    def _getDirectionKey(self, params):
        for key in params.keys():
            if key.startswith("upPA"):
                return key.split("_")
            elif key.startswith("downPA"):
                return key.split("_")
            elif key.startswith("upCA"):
                return key.split("_")
            elif key.startswith("downCA"):
                return key.split("_")
        return None

    def _checkParams(self,params):
        RHConfModifCFABase._checkParams(self,params)
        toNorm=["auth_prim_id","auth_prim_title", "auth_prim_first_name",
            "auth_prim_family_name","auth_prim_affiliation",
            "auth_prim_email", "auth_prim_phone", "auth_prim_speaker",
            "auth_co_id","auth_co_title", "auth_co_first_name",
            "auth_co_family_name","auth_co_affiliation",
            "auth_co_email", "auth_co_phone", "auth_co_speaker"]
        for k in toNorm:
            params[k]=self._normaliseListParam(params.get(k,[]))
        self._abstractData=abstractDataWrapper.Abstract(self._conf.getAbstractMgr().getAbstractFieldsMgr(), **params)
        self._action=""
        if params.has_key("OK"):
            self._action="CREATE"
        elif params.has_key("CANCEL"):
            self._action="CANCEL"
        elif params.has_key("addPrimAuthor"):
            self._abstractData.newPrimaryAuthor()
        elif params.has_key("addCoAuthor"):
            self._abstractData.newCoAuthor()
        elif params.has_key("remPrimAuthors"):
            idList=self._normaliseListParam(params.get("sel_prim_author",[]))
            self._abstractData.removePrimaryAuthors(idList)
        elif params.has_key("remCoAuthors"):
            idList=self._normaliseListParam(params.get("sel_co_author",[]))
            self._abstractData.removeCoAuthors(idList)
        else:
            arrowKey = self._getDirectionKey(params)
            if arrowKey != None:
                id = arrowKey[1]
                if arrowKey[0] == "upPA":
                    self._abstractData.upPrimaryAuthors(id)
                elif arrowKey[0] == "downPA":
                    self._abstractData.downPrimaryAuthors(id)
                elif arrowKey[0] == "upCA":
                    self._abstractData.upCoAuthors(id)
                elif arrowKey[0] == "downCA":
                    self._abstractData.downCoAuthors(id)
            else:
                self._abstractData=abstractDataWrapper.Abstract(self._conf.getAbstractMgr().getAbstractFieldsMgr())

    def _process( self ):
        if self._action=="CREATE":
            if not self._abstractData.hasErrors():
                abs=self._target.getAbstractMgr().newAbstract(self._getUser())
                self._abstractData.updateAbstract(abs)
                self._redirect(urlHandlers.UHAbstractManagment.getURL(abs))
                return
        elif self._action=="CANCEL":
            self._redirect(urlHandlers.UHConfAbstractManagment.getURL(self._target))
            return
        p = conferences.WPModNewAbstract(self,self._target,self._abstractData)
        return p.display()


class RHContribsActions:
    """
    class to select the action to do with the selected abstracts
    """
    def __init__(self, req):
        self._req = req

    def process(self, params):
        if params.has_key("PDF"):
            return RHContribsToPDF(self._req).process(params)
        elif params.has_key("AUTH"):
            return RHContribsParticipantList(self._req).process(params)
        elif params.has_key("move"):
            return RHMoveContribsToSession(self._req).process(params)
        elif params.has_key("PKG"):
            return RHMaterialPackage(self._req).process(params)
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
            filename = "%s - Book of abstracts.pdf"%self._target.getTitle()
            pdf = ContributionBook(self._target, self._contribs, self.getAW(),tz=tz)
            data = pdf.getPDFBin()
            self._req.headers_out["Content-Length"] = "%s"%len(data)
            cfg = Config.getInstance()
            mimetype = cfg.getFileTypeMimeType( "PDF" )
            self._req.content_type = """%s"""%(mimetype)
            self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
            return data

        elif self._displayType == "bookOfAbstractBoardNo":
            tz = self._target.getTimezone()
            filename = "%s - Book of abstracts.pdf"%self._target.getTitle()
            pdf = ContributionBook(self._target, self._contribs, self.getAW(),tz=tz, sortedBy="boardNo")
            data = pdf.getPDFBin()
            self._req.headers_out["Content-Length"] = "%s"%len(data)
            cfg = Config.getInstance()
            mimetype = cfg.getFileTypeMimeType( "PDF" )
            self._req.content_type = """%s"""%(mimetype)
            self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
            return data

        elif self._displayType == "ContributionList":
            tz = self._conf.getTimezone()
            filename = "Contributions.pdf"
            if not self._contribs:
                return "No contributions to print"
            pdf = ConfManagerContribsToPDF(self._conf, self._contribs, tz=tz)
            data = pdf.getPDFBin()
            #self._req.headers_out["Accept-Ranges"] = "bytes"
            self._req.set_content_length(len(data))
            #self._req.headers_out["Content-Length"] = "%s"%len(data)
            cfg = Config.getInstance()
            mimetype = cfg.getFileTypeMimeType( "PDF" )
            self._req.content_type = """%s"""%(mimetype)
            self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
            return data


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
        pdf = ConfManagerContribsToPDF(self._conf, self._contribs, tz=tz)
        data = pdf.getPDFBin()
        #self._req.headers_out["Accept-Ranges"] = "bytes"
        self._req.set_content_length(len(data))
        #self._req.headers_out["Content-Length"] = "%s"%len(data)
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "PDF" )
        self._req.content_type = """%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
        return data

class RHContribsParticipantList(RHConferenceModifBase):

    #def _checkProtection( self ):
    #    if len( self._conf.getCoordinatedTracks( self._getUser() ) ) == 0:
    #        RHConferenceModifBase._checkProtection( self )

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
            return  _("""<table align=\"center\" width=\"100%%\"><tr><td> _("There are no contributions") </td></tr></table>""")

        speakers = OOBTree()
        primaryAuthors = OOBTree()
        coAuthors = OOBTree()
        speakerEmails = Set()
        primaryAuthorEmails = Set()
        coAuthorEmails = Set()

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
                contribList.append(contrib)
            for contrib in contribList:
                contrib.setSession(self._session)
            self._redirect(url)
            return
        p=conferences.WPModMoveContribsToSession(self,self._target)
        return p.display(contribIds=self._contribIds)


class RHMaterialPackage(RHConferenceModifBase):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._contribIds = self._normaliseListParam( params.get("contributions", []) )
        self._contribs = []
        for id in self._contribIds:
            self._contribs.append(self._conf.getContributionById(id))

    def _process( self ):
        if not self._contribs:
            return "No contribution selected"
        p=ContribPacker(self._conf)
        path=p.pack(self._contribs,["paper","slides"],ZIPFileHandler())
        filename = "material.zip"
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "ZIP" )
        self._req.content_type = """%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
        self._req.sendfile(path)

class RHProceedings(RHConferenceModifBase):

    def _process( self ):
        p=ProceedingsPacker(self._conf)
        path=p.pack(ZIPFileHandler())
        filename = "proceedings.zip"
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType( "ZIP" )
        self._req.content_type = """%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
        self._req.sendfile(path)


class RHAbstractBook( RHConfModifCFABase ):
    _uh = urlHandlers.UHConfModAbstractBook

    def _checkParams( self, params ):
        RHConfModifCFABase._checkParams( self, params )

    def _process( self ):
        p = conferences.WPModAbstractBook(self,self._target)
        return p.display()


class RHAbstractBookEdit( RHConfModifCFABase ):
    _uh = urlHandlers.UHConfModAbstractBookEdit

    def _checkParams( self, params ):
        RHConfModifCFABase._checkParams( self, params )
        self._action=""
        if params.has_key("EDIT"):
            self._action="EDIT"
            self._text=params.get("text","")
        elif params.has_key("CANCEL"):
            self._action="CANCEL"

    def _process( self ):
        url=urlHandlers.UHConfModAbstractBook.getURL(self._target)
        if self._action=="CANCEL":
            self._redirect(url)
            return
        elif self._action=="EDIT":
            self._target.getBOAConfig().setText(self._text)
            self._redirect(url)
            return
        p=conferences.WPModAbstractBookEdit(self,self._target)
        return p.display()

class RHFullMaterialPackage(RHConferenceModifBase):
    _uh=urlHandlers.UHConfModFullMaterialPackage

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._errors = params.get("errors","")

    def _process( self ):
        p = conferences.WPFullMaterialPackage(self,self._target)
        return p.display(errors=self._errors)


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
            if self._materialTypes != []:
                p=ConferencePacker(self._conf, self._aw)
                path=p.pack(self._materialTypes, self._days, self._mainResource, self._fromDate, ZIPFileHandler(),self._sessionList)
                filename = "full-material.zip"
                cfg = Config.getInstance()
                mimetype = cfg.getFileTypeMimeType( "ZIP" )
                self._req.content_type = """%s"""%(mimetype)
                self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
                self._req.sendfile(path)
            else:
                url = urlHandlers.UHConfModFullMaterialPackage.getURL(self._conf)
                url.addParam("errors", "You have to select at least one material type")
                self._redirect( url )
        else:
            self._redirect( urlHandlers.UHConfModifTools.getURL( self._conf ) )

class RHConfDVDCreation(RHConferenceModifBase):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._create=params.has_key("confirm")
        self._confirmed=params.has_key("confirm") or params.has_key("cancel")

    def _process( self ):
        if self._confirmed:
            if self._create:
                DVDCreation(self, self._conf, self.getWebFactory()).create()
                self._redirect( urlHandlers.UHDVDDone.getURL( self._conf ) )
            else:
                self._redirect( urlHandlers.UHConfModifTools.getURL( self._conf ) )
        else:
            wp = conferences.WPConfModifDVDCreationConfirm(self, self._conf)
            return wp.display()

class RHConfDVDDone(RHConferenceModifBase):

    def _process( self ):
        url=urlHandlers.UHConfModifTools.getURL(self._conf)
        p = conferences.WPDVDDone(self, self._conf)
        return p.display(url=url)

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

class RHConfSectionsSettings( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfSectionsSettings

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._sectionId = params.get("sectionId", "")
        if self._sectionId.strip()!="":
            if not conference.ConfSectionsMgr().hasSection(self._sectionId):
                raise MaKaCError( _("The section that you are trying to enable/disable does not exist"))


    def _process( self ):
        if self._sectionId.strip() != "":
            if self._conf.hasEnabledSection(self._sectionId):
                self._conf.disableSection(self._sectionId)
            else:
                self._conf.enableSection(self._sectionId)
        self._redirect(urlHandlers.UHConferenceModification.getURL(self._conf))

class RHConfModifPendingQueues( RHConferenceModifBase ):
    _uh = urlHandlers.UHConfModifPendingQueues

    def _process( self ):
        p = conferences.WPConfModifPendingQueues( self, self._target, self._getRequestParams().get("tab","submitters") )
        return p.display()

class RHConfModifPendingQueuesActionSubm:
    """
    class to select the action to do with the selected pending submitters
    """

    _uh = urlHandlers.UHConfModifPendingQueuesActionSubm

    def __init__(self, req):
        self._req = req

    def process(self, params):
        if params.has_key("remove"):
            return RHConfModifPendingQueuesRemoveSubm(self._req).process(params)
        elif params.has_key("reminder"):
            return RHConfModifPendingQueuesReminderSubm(self._req).process(params)
        return "no action to do"

class RHConfModifPendingQueuesRemoveSubm( RHConferenceModifBase ):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._pendingSubmIds = self._normaliseListParam( params.get("pendingSubmitters", []) )
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
        self._pendingSubmIds = self._normaliseListParam( params.get("pendingSubmitters", []) )
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
        self._req = req

    def process(self, params):
        if params.has_key("remove"):
            return RHConfModifPendingQueuesRemoveMgr(self._req).process(params)
        elif params.has_key("reminder"):
            return RHConfModifPendingQueuesReminderMgr(self._req).process(params)
        return "no action to do"

class RHConfModifPendingQueuesRemoveMgr( RHConferenceModifBase ):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._pendingMgrIds = self._normaliseListParam( params.get("pendingManagers", []) )
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
        self._pendingMgrIds = self._normaliseListParam( params.get("pendingManagers", []) )
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
        self._req = req

    def process(self, params):
        if params.has_key("remove"):
            return RHConfModifPendingQueuesRemoveCoord(self._req).process(params)
        elif params.has_key("reminder"):
            return RHConfModifPendingQueuesReminderCoord(self._req).process(params)
        return "no action to do"

class RHConfModifPendingQueuesRemoveCoord( RHConferenceModifBase ):

    def _checkParams( self, params ):
        RHConferenceModifBase._checkParams( self, params )
        self._pendingCoordIds = self._normaliseListParam( params.get("pendingCoordinators", []) )
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
        self._pendingCoordIds = self._normaliseListParam( params.get("pendingCoordinators", []) )
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

class RHConfAddAbstractField( RHConfModifCFABase ):
    _uh = urlHandlers.UHConfModifCFAAddOptFld

    def _checkParams( self, params ):
        RHConfModifCFABase._checkParams( self, params )
        self._fieldId = ""

    def _process( self ):
        p = conferences.WPConfModifCFAAddField( self, self._target, self._fieldId )
        return p.display()

class RHConfEditAbstractField( RHConfModifCFABase ):
    _uh = urlHandlers.UHConfModifCFAEditOptFld

    def _checkParams( self, params ):
        RHConfModifCFABase._checkParams( self, params )
        self._fieldId = params.get("fieldId", "")

    def _process( self ):
        p = conferences.WPConfModifCFAAddField( self, self._target, self._fieldId )
        return p.display()

class RHConfPerformAddAbstractField( RHConfModifCFABase ):
    _uh = urlHandlers.UHConfModifCFAPerformAddOptFld

    def _checkParams( self, params ):
        RHConfModifCFABase._checkParams( self, params )
        self._cancel = params.get("cancel",None)
        if self._cancel:
            return
        self._fieldId = params.get("fieldId", "")
        self._fieldName = params.get("fieldName", "")
        self._fieldCaption = params.get("fieldCaption", "")
        self._fieldMaxLength = params.get("fieldMaxLength", 0)
        self._fieldIsMandatory = params.get("fieldIsMandatory", False)
        self._fieldType = params.get("fieldType", "textarea")
        if self._fieldIsMandatory == "Yes":
            self._fieldIsMandatory = True
        else:
            self._fieldIsMandatory = False
        if self._fieldName == "":
            raise MaKaCError( _("The field name must not be empty"))

    def _process( self ):
        if not self._cancel:
            id=self._conf.getAbstractMgr().addAbstractField(self._fieldId, self._fieldName, self._fieldCaption, self._fieldMaxLength, self._fieldIsMandatory, self._fieldType)
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



class RHConfModifSelectChairs(RHConferenceModifBase):

    def _process( self ):
        p = conferences.WPConfModifSelectChairs( self, self._target )
        return p.display( **self._getRequestParams() )


class RHConfModifAddChairs(RHConferenceModifBase):

    def _newChair(self, av):
        chair=conference.ConferenceChair()
        chair.setTitle(av.getTitle())
        chair.setFirstName(av.getFirstName())
        chair.setFamilyName(av.getSurName())
        chair.setAffiliation(av.getAffiliation())
        chair.setEmail(av.getEmail())
        chair.setAddress(av.getAddress())
        chair.setPhone(av.getTelephone())
        chair.setFax(av.getFax())
        self._target.addChair(chair)

    def _process( self ):
        params = self._getRequestParams()
        if "selectedPrincipals" in params and not "cancel" in params:
            ah = user.AvatarHolder()
            for id in self._normaliseListParam( params["selectedPrincipals"] ):
                av=ah.getById( id )
                self._newChair(av)
        self._redirect( urlHandlers.UHConferenceModification.getURL( self._target ) )

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

class RHReschedule(RHConferenceModifBase):

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self._cancel=params.has_key("CANCEL")
        self._ok=params.has_key("OK")
        self._hour=params.get("hour","")
        self._minute=params.get("minute","")
        self._action=params.get("action","duration")
        self._targetDay=params.get("targetDay",None) #comes in format YYYYMMDD, ex: 20100317
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
                p=conferences.WPConfModifReschedule(self,self._conf, self._targetDay)
                return p.display()
            else:
                t=timedelta(hours=int(self._hour), minutes=int(self._minute))
                self._conf.getSchedule().rescheduleTimes(self._action, t, self._day)
        self._redirect("%s#%s"%(urlHandlers.UHConfModifSchedule.getURL(self._conf), self._targetDay))

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

class RHConfModfReportNumberEdit(RHConferenceModifBase):

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self._reportNumberSystem=params.get("reportNumberSystem","")

    def _process(self):
        if self._reportNumberSystem!="":
            p=conferences.WPConfModifReportNumberEdit(self,self._conf, self._reportNumberSystem)
            return p.display()
        else:
            self._redirect(urlHandlers.UHConferenceModification.getURL( self._conf ))

class RHConfModfReportNumberPerformEdit(RHConferenceModifBase):

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self._reportNumberSystem=params.get("reportNumberSystem","")
        self._reportNumber=params.get("reportNumber","")

    def _process(self):
        if self._reportNumberSystem!="" and self._reportNumber!="":
            self._conf.getReportNumberHolder().addReportNumber(self._reportNumberSystem, self._reportNumber)
        self._redirect("%s#reportNumber"%urlHandlers.UHConferenceModification.getURL( self._conf ))


class RHConfModfReportNumberRemove(RHConferenceModifBase):

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self._reportNumberIdsToBeDeleted=self._normaliseListParam( params.get("deleteReportNumber",[]))

    def _process(self):
        nbDeleted = 0
        for id in self._reportNumberIdsToBeDeleted:
            self._conf.getReportNumberHolder().removeReportNumberById(int(id)-nbDeleted)
            nbDeleted += 1
        self._redirect("%s#reportNumber"%urlHandlers.UHConferenceModification.getURL( self._conf ))



class RHMaterialsAdd(RHConferenceModifBase):
    _uh = urlHandlers.UHConfModifAddMaterials

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        if not hasattr(self,"_rhSubmitMaterial"):
            self._rhSubmitMaterial=RHSubmitMaterialBase(self._target, self)
        self._rhSubmitMaterial._checkParams(params)

    def _process( self ):
        if self._target.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p.display()
        else:
            r=self._rhSubmitMaterial._process(self, self._getRequestParams())
        if r is None:
            self._redirect(self._uh.getURL(self._target))

        return r

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

from MaKaC.webinterface.rh.roomBooking import RHRoomBookingSearch4Rooms
from MaKaC.webinterface.rh.roomBooking import RHRoomBookingRoomList
from MaKaC.webinterface.rh.roomBooking import RHRoomBookingBookingList
from MaKaC.webinterface.rh.roomBooking import RHRoomBookingRoomDetails
from MaKaC.webinterface.rh.roomBooking import RHRoomBookingBookingDetails
from MaKaC.webinterface.rh.roomBooking import RHRoomBookingBookingForm
from MaKaC.webinterface.rh.roomBooking import RHRoomBookingSaveBooking

# 0. RHConfModifRoomBookingChooseEvent

class RHConferenceModifRoomBookingBase( RoomBookingDBMixin, RHConferenceModifBase ):

    def _checkProtection( self ):
        self._checkSessionUser()
        RHConferenceModifBase._checkProtection(self)

class RHConfModifRoomBookingChooseEvent( RHConferenceModifRoomBookingBase, RHRoomBookingSearch4Rooms ):
    _uh = urlHandlers.UHConfModifRoomBookingChooseEvent

    def _checkParams( self, params ):
        locator = locators.WebLocator()
        locator.setConference( params )
        self._conf = locator.getConference()
        self._setMenuStatus( params )
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

        websession = self._websession

        # No example given? Fall back to general defaults
        if self._dontAssign:
            return

        if self._conf != None and self._conf.getRoom() and self._conf.getRoom().getName():
            self._eventRoomName = self._conf.getRoom().getName()

        # Copy values from   Session
        if self._conf != None  and  self._assign2Session != None:
            session = self._assign2Session
            websession.setVar( "defaultStartDT", session.getAdjustedStartDate().replace(tzinfo=None) )
            websession.setVar( "defaultEndDT", session.getAdjustedEndDate().replace(tzinfo=None) )
            if session.getStartDate().date() != session.getEndDate().date():
                websession.setVar( "defaultRepeatability", RepeatabilityEnum.daily )
            else:
                websession.setVar( "defaultRepeatability", None )
            websession.setVar( "defaultBookedForName", self._getUser().getFullName() + " | " + session.getTitle() )
            websession.setVar( "defaultReason", "Session '" + session.getTitle() + "'" )
            return

        # Copy values from   Contribution
        if self._conf != None  and  self._assign2Contribution != None:
            contrib = self._assign2Contribution
            websession.setVar( "defaultStartDT", contrib.getAdjustedStartDate().replace(tzinfo=None) )
            websession.setVar( "defaultEndDT", contrib.getAdjustedEndDate().replace(tzinfo=None) )
            if contrib.getStartDate().date() != contrib.getEndDate().date():
                websession.setVar( "defaultRepeatability", RepeatabilityEnum.daily )
            else:
                websession.setVar( "defaultRepeatability", None )
            websession.setVar( "defaultBookedForName", self._getUser().getFullName() + " | " + contrib.getTitle() )
            websession.setVar( "defaultReason", "Contribution '" + contrib.getTitle() + "'" )
            return

        # Copyt values from   Conference / Meeting / Lecture
        if self._conf != None:
            conf = self._conf
            websession.setVar( "defaultStartDT", conf.getAdjustedStartDate().replace(tzinfo=None) )
            websession.setVar( "defaultEndDT", conf.getAdjustedEndDate().replace(tzinfo=None) )
            if conf.getStartDate().date() != conf.getEndDate().date():
                websession.setVar( "defaultRepeatability", RepeatabilityEnum.daily )
            else:
                websession.setVar( "defaultRepeatability", None )
            if self._getUser():
                websession.setVar( "defaultBookedForName", self._getUser().getFullName() + " | " + conf.getTitle() )
            else:
                websession.setVar( "defaultBookedForName", conf.getTitle() )
            websession.setVar( "defaultReason", conf.getVerboseType() + " '" + conf.getTitle() + "'" )
            return

    def _checkParams( self, params ):
        locator = locators.WebLocator()
        locator.setConference( params )
        self._conf = locator.getConference()

        RHRoomBookingSearch4Rooms._checkParams( self, params )
        self._forNewBooking = True

        if params.get( 'sessionId' ):
            self._assign2Session = self._conf.getSessionById( params['sessionId'] )
            self._websession.setVar( "assign2Session", self._assign2Session )
        else:
            self._assign2Session = None
        if params.get( 'contribId' ):
            self._assign2Session = None
            self._assign2Contribution = self._conf.getContributionById( params['contribId'] )
            self._websession.setVar( "assign2Contribution", self._assign2Contribution )
        else:
            self._assign2Contribution = None
        self._dontAssign = params.get( 'dontAssign' ) == "True"
        self._websession.setVar( "dontAssign", self._dontAssign )

        self._setDefaultFormValues()

        self._setMenuStatus( params )
        RHConferenceModifRoomBookingBase._checkParams( self, params )

    def _process( self ):
        self._businessLogic()
        for room in self._rooms:
            room.setOwner( self._conf )

        p = conferences.WPConfModifRoomBookingSearch4Rooms( self )
        return p.display()

# 2. List of...

class RHConfModifRoomBookingRoomList( RHConferenceModifRoomBookingBase, RHRoomBookingRoomList ):
    _uh = urlHandlers.UHConfModifRoomBookingRoomList

    def _checkParams( self, params ):
        locator = locators.WebLocator()
        locator.setConference( params )
        self._conf = locator.getConference()
        self._target = self._conf
        self._setMenuStatus( params )

        RHRoomBookingRoomList._checkParams( self, params )

    def _process( self ):
        if self._target.isClosed():
            p = conferences.WPConfModifClosed( self, self._target )
            return p.display()

        self._businessLogic()
        for room in self._rooms:
            if room.getOwner() == None:
                room.setOwner( self._conf )

        p = conferences.WPConfModifRoomBookingRoomList( self )
        return p.display()

class RHConfModifRoomBookingList( RHConferenceModifRoomBookingBase, RHRoomBookingBookingList ):
    _uh = urlHandlers.UHConfModifRoomBookingList

    def _checkParams( self, params ):
        RHConferenceModifRoomBookingBase._checkParams(self, params)
        RHRoomBookingBookingList._checkParams(self, params)

        locator = locators.WebLocator()
        locator.setConference( params )
        self._conf = self._target = locator.getConference()
        self._setMenuStatus( params )

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
        RHRoomBookingRoomDetails._checkParams( self, params )

        locator = locators.WebLocator()
        locator.setConference( params )
        self._conf = locator.getConference()
        self._setMenuStatus( params )

        self._target = self._conf

    def _process( self ):
        self._businessLogic()
        self._room.setOwner( self._conf )
        p = conferences.WPConfModifRoomBookingRoomDetails( self )
        return p.display()

class RHConfModifRoomBookingDetails( RHConferenceModifRoomBookingBase, RHRoomBookingBookingDetails ):
    _uh = urlHandlers.UHConfModifRoomBookingDetails

    def _checkParams( self, params ):
        locator = locators.WebLocator()
        locator.setConference( params )
        self._conf = locator.getConference()
        self._setMenuStatus( params )

        RHRoomBookingBookingDetails._checkParams( self, params )
        self._target = self._conf

    def _process( self ):
        self._businessLogic()
        self._resv.setOwner( self._conf )
        self._resv.room.setOwner( self._conf )

        p = conferences.WPConfModifRoomBookingDetails( self )
        return p.display()

# 4. New ...

class RHConfModifRoomBookingBookingForm( RHConferenceModifRoomBookingBase, RHRoomBookingBookingForm ):
    _uh = urlHandlers.UHConfModifRoomBookingBookingForm

    def _checkParams( self, params ):
        RHRoomBookingBookingForm._checkParams( self, params )

        locator = locators.WebLocator()
        locator.setConference( params )
        self._conf = locator.getConference()
        self._target = self._conf     #self._candResv
        self._setMenuStatus( params )

    def _process( self ):
        self._businessLogic()
        self._candResv.room.setOwner( self._conf )
        self._candResv.setOwner( self._conf )
        p = conferences.WPConfModifRoomBookingBookingForm( self )
        return p.display()

class RHConfModifRoomBookingSaveBooking( RHConferenceModifRoomBookingBase, RHRoomBookingSaveBooking ):
    _uh = urlHandlers.UHConfModifRoomBookingSaveBooking

    def _checkParams( self, params ):
        RHRoomBookingSaveBooking._checkParams( self, params )

        locator = locators.WebLocator()
        locator.setConference( params )
        self._conf = locator.getConference()
        self._target = self._conf

        # Assign room to event / session / contribution?
        websession = self._websession
        self._assign2Session = websession.getVar( "assign2Session" ) # Session or None
        self._assign2Contribution = websession.getVar( "assign2Contribution" ) # Contribution or None
        self._assign2Conference = None
        if not self._assign2Session  and  not self._assign2Contribution:
            if self._conf  and  websession.getVar( "dontAssign" ) != "True": # 'True' or None
                self._assign2Conference = self._conf

        self._setMenuStatus( params )

    def _process( self ):
        self._candResv.room.setOwner( self._conf )
        self._businessLogic()

        if self._thereAreConflicts:
            url = urlHandlers.UHConfModifRoomBookingBookingForm.getURL( self._candResv.room )
            self._redirect( url )
        else:
            # Add it to event reservations list
            guid = ReservationGUID( Location.parse( self._candResv.locationName ), self._candResv.id )
            self._conf.addRoomBookingGuid( guid )

            # Set room for event / session / contribution (always only _one_ available)
            assign2 = self._assign2Conference or self._assign2Contribution or self._assign2Session
            croom = CustomRoom()         # Boilerplate class, has only 'name' attribute
            croom.setName( self._candResv.room.name )
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
"""
Badge Design and Printing classes
"""
class RHConfBadgePrinting(RHConferenceModifBase):
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
        self.__new = params.get("new","False") == "True"
        self.__cancel = params.get("cancel","False") == "True"

    def _process(self):
        if self._target.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
        else:
            if self.__templateId and self.__templateData and not self.__deleteTemplateId:

                if self.__new:
                    self._target.getBadgeTemplateManager().storeTemplate(self.__templateId, self.__templateData)
                    key = "tempBackground", self._conf.id, self.__templateId
                    filePaths = self._getSession().getVar(key)
                    if filePaths != None:
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
                    key = "tempBackground", self._conf.id, self.__templateId
                    self._getSession().removeVar(key)


            if self._target.getId() == "default":
                p = admins.WPBadgeTemplates(self)
            else:
                p = conferences.WPConfModifBadgePrinting(self, self._target)

        return p.display()

class RHConfBadgeDesign(RHConferenceModifBase):
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
            p = conferences.WPConfModifBadgeDesign(self, self._target, self.__templateId, self.__new, self.__baseTemplate)
        return p.display()

class RHConfBadgePrintingPDF(RHConferenceModifBase):
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
        RHConferenceModifBase._checkParams(self, params)

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


            filename = "Badges.pdf"

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
                                             self.__registrantList)
            data = pdf.getPDFBin()
            #self._req.headers_out["Accept-Ranges"] = "bytes"
            self._req.set_content_length(len(data))
            #self._req.headers_out["Content-Length"] = "%s"%len(data)
            cfg = Config.getInstance()
            mimetype = cfg.getFileTypeMimeType( "PDF" )
            self._req.content_type = """%s"""%(mimetype)
            self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
            return data

class RHConfBadgeSaveTempBackground(RHConferenceModifBase):
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

    def _saveFileToTemp( self, fd ):
        fileName = self._getNewTempFile()
        f = open( fileName, "wb" )
        f.write( fd.read() )
        f.close()
        return os.path.split(fileName)[-1]

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.__templateId = params.get("templateId",None)
        try:
            self._tempFilePath = self._saveFileToTemp( params["file"].file )
        except AttributeError:
            self._tempFilePath = None

    def _process(self):
        if self._target.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p
        else:
            if self._tempFilePath is not None:
                if self._conf.getBadgeTemplateManager().hasTemplate(self.__templateId):
                    backgroundId = self._conf.getBadgeTemplateManager().getTemplateById(self.__templateId).addTempBackgroundFilePath(self._tempFilePath)
                else:
                    key = "tempBackground", self._conf.id, self.__templateId
                    value = self._getSession().getVar(key)
                    if value == None:
                        tempFilePathList = PersistentList()
                        tempFilePathList.append(self._tempFilePath)
                        self._getSession().setVar(key, tempFilePathList)
                        backgroundId = 0
                    else:
                        value.append(self._tempFilePath)
                        backgroundId = len(value) - 1


                return "".join(['<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">',
                                '<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"></head><body>',
                                '<span id="background id">',
                                  str(backgroundId),
                                  '</span>',
                                  '<span id="background url">',
                                  str(urlHandlers.UHConfModifBadgeGetBackground.getURL(self._conf, self.__templateId, backgroundId)),
                                  '</span>',
                                  '</body></html>'
                                  ])

class RHConfBadgeGetBackground(RHConferenceModifBase):
    """ Class used to obtain a background in order to display it
        on the Badge Design screen.
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
        self._req.headers_out["Content-Length"]="%s"%image.getSize()
        cfg=Config.getInstance()
        mimetype=cfg.getFileTypeMimeType(image.getFileType())
        self._req.content_type="""%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"]="""inline; filename="%s\""""%image.getFileName()
        return image.readBin()

    def __fileBin(self, filePath):
        file = open(filePath, "rb")
        size = int(os.stat(filePath)[stat.ST_SIZE])
        self._req.headers_out["Content-Length"]="%s"%size
        self._req.content_type="""%s"""%("unknown")
        self._req.headers_out["Content-Disposition"]="""inline; filename="%s\""""%"tempBackground"
        r = file.read()
        file.close()
        return r

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
                key = "tempBackground", self._conf.id, self.__templateId
                filePath = os.path.join(tempPath,self._getSession().getVar(key) [ int(self.__backgroundId) ])
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
            p = conferences.WPConferenceModificationClosed( self, self._target )
        else:
            if self.__templateId and self.__templateData and not self.__deleteTemplateId:
                if self.__new:
                # template is new
                    self._target.getPosterTemplateManager().storeTemplate(self.__templateId, self.__templateData)
                    key = "tempBackground", self._conf.id, self.__templateId
                    filePaths = self._getSession().getVar(key)
                    if filePaths != None:
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
                    fkey = "tempBackground", self._conf.id, self.__templateId
                    self._getSession().removeVar(fkey)

            if self._target.getId() == "default":
                p = admins.WPPosterTemplates(self)
            else:
                p = conferences.WPConfModifPosterPrinting(self, self._target)
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
            filename = "Poster.pdf"
            pdf = LectureToPosterPDF(self._conf,
                                             self.__template,
                                             self.__marginH,
                                             self.__marginV,
                                             self.__pagesize)

            data = pdf.getPDFBin()
            #self._req.headers_out["Accept-Ranges"] = "bytes"
            self._req.set_content_length(len(data))
            #self._req.headers_out["Content-Length"] = "%s"%len(data)
            cfg = Config.getInstance()
            mimetype = cfg.getFileTypeMimeType( "PDF" )
            self._req.content_type = """%s"""%(mimetype)
            self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
            return data

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

    def _saveFileToTemp( self, fd ):
        fileName = self._getNewTempFile()
        f = open( fileName, "wb" )
        f.write( fd.read() )
        f.close()
        return os.path.split(fileName)[-1]

    def _checkParams(self, params):
        RHConferenceModifBase._checkParams(self, params)
        self.__templateId = params.get("templateId",None)

        self._bgPosition = params.get("bgPosition",None)

        try:
            self._tempFilePath = self._saveFileToTemp( params["file"].file )
        except AttributeError:
            self._tempFilePath = None

    def _process(self):

        if self._target.isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p
        else:
            if self._tempFilePath is not None:
                if self._conf.getPosterTemplateManager().hasTemplate(self.__templateId):
                # Save
                    backgroundId = self._conf.getPosterTemplateManager().getTemplateById(self.__templateId).addTempBackgroundFilePath(self._tempFilePath,self._bgPosition)
                else:
                # New
                    key = "tempBackground", self._conf.id, self.__templateId

                    value = self._getSession().getVar(key)
                    if value == None:
                    # First background
                        tempFilePathList = PersistentList()
                        tempFilePathList.append((self._tempFilePath,self._bgPosition))
                        self._getSession().setVar(key, tempFilePathList)
                        backgroundId = 0
                    else:
                    # We have more
                        value.append((self._tempFilePath,self._bgPosition))
                        backgroundId = len(value) - 1



                return "".join(['<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">',
                                '<html><head><meta http-equiv="Content-Type" content="text/html; charset=utf-8"></head><body>',
                                '<span id="background id">',
                                  str(backgroundId),
                                  '</span>',
                                  '<span id="background url">',
                                  str(urlHandlers.UHConfModifPosterGetBackground.getURL(self._conf, self.__templateId, backgroundId)),
                                  '</span>',
                                  '<span id="background pos">',
                                  str(self._bgPosition),
                                  '</span>',

                                  '</body></html>'
                                  ])

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
        self._req.headers_out["Content-Length"]="%s"%image.getSize()
        cfg=Config.getInstance()
        mimetype=cfg.getFileTypeMimeType(image.getFileType())
        self._req.content_type="""%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"]="""inline; filename="%s\""""%image.getFileName()
        return image.readBin()

    def __fileBin(self, filePath):
        file = open(filePath, "rb")
        size = int(os.stat(filePath)[stat.ST_SIZE])
        self._req.headers_out["Content-Length"]="%s"%size
        self._req.content_type="""%s"""%("unknown")
        self._req.headers_out["Content-Disposition"]="""inline; filename="%s\""""%"tempBackground"
        r = file.read()
        file.close()
        return r

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
                key = "tempBackground", self._conf.id, self.__templateId

                filePath = os.path.join(tempPath, self._getSession().getVar(key) [ int(self.__backgroundId) ][0])
                return self.__fileBin(filePath)