# -*- coding: utf-8 -*-
##
##
## This file is part of Indico.
## Copyright (C) 2002 - 2013 European Organization for Nuclear Research (CERN).
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
from flask import session

import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.pages.registrationForm as registrationForm
import MaKaC.webinterface.rh.conferenceModif as conferenceModif
from MaKaC.errors import FormValuesError,MaKaCError, ConferenceClosedError
from datetime import datetime
from MaKaC.common import utils
from MaKaC.i18n import _

# indico legacy imports
from MaKaC.services.implementation.base import AdminService, ParameterManager, \
     ServiceError


class RHRegistrationFormModifBase( conferenceModif.RHConferenceModifBase ):

    def _checkProtection( self ):
        if not self._target.canManageRegistration(self.getAW().getUser()):
            conferenceModif.RHConferenceModifBase._checkProtection(self)
        if self._target.getConference().isClosed():
            raise ConferenceClosedError(self._target.getConference())


class RHRegistrationPreview ( RHRegistrationFormModifBase ):

    def _process( self ):
        p = registrationForm.WPConfModifRegFormPreview( self, self._conf )
        return p.display()

class RHRegistrationFormModif( RHRegistrationFormModifBase ):
    _uh = urlHandlers.UHConfModifRegForm

    def _process( self ):
        p = registrationForm.WPConfModifRegForm( self, self._conf )
        return p.display()

class RHRegistrationFormModifChangeStatus( RHRegistrationFormModifBase ):

    def _checkParams( self, params ):
        RHRegistrationFormModifBase._checkParams( self, params )
        self._newStatus = params["changeTo"]

    def _process( self ):
        regForm = self._conf.getRegistrationForm()
        if self._newStatus == "True":
            regForm.activate()
        else:
            regForm.deactivate()
        self._redirect(urlHandlers.UHConfModifRegForm.getURL(self._conf))

class RHRegistrationFormModifDataModification( RHRegistrationFormModifBase ):

    def _process( self ):
        p = registrationForm.WPConfModifRegFormDataModification( self, self._conf )
        return p.display()

class RHRegistrationFormModifPerformDataModification( RHRegistrationFormModifBase ):

    def _checkParams( self, params ):
        RHRegistrationFormModifBase._checkParams( self, params )
        self._cancel = params.has_key("cancel")

        try:
            self._extraTimeAmount = int(params.get("extraTimeAmount"))
        except ValueError:
            raise FormValuesError(_("The extra allowed time amount is not a valid integer number!"))

        self._extraTimeUnit = params.get("extraTimeUnit")
        if self._extraTimeUnit not in ['days', 'weeks']:
            raise FormValuesError(_("The extra allowed time unit is not valid!"))

    def _process( self ):
        if not self._cancel:
            regForm = self._conf.getRegistrationForm()
            params = self._getRequestParams()
            try:
                sDate = datetime( int( params["sYear"] ), \
                                  int( params["sMonth"] ), \
                                  int( params["sDay"] ) )
            except ValueError,e:
                raise FormValuesError("The start date you have entered is not correct: %s"%e, "RegistrationForm")
            try:
                eDate = datetime( int( params["eYear"] ), \
                                  int( params["eMonth"] ), \
                                  int( params["eDay"] ) )
            except ValueError,e:
                raise FormValuesError("The end date you have entered is not correct: %s"%e, "RegistrationForm")
            if eDate < sDate :
                raise FormValuesError("End date can't be before start date!", "RegistrationForm")
            try:
                meDate = None
                if params["meYear"] or params["meMonth"] or params["meDay"]:
                    meDate = datetime( int( params["meYear"] ), \
                                  int( params["meMonth"] ), \
                                  int( params["meDay"] ) )
            except ValueError,e:
                raise FormValuesError("The modification end date you have entered is not correct: %s"%e, "RegistrationForm")
            if meDate is not None and (meDate < sDate or meDate < eDate):
                raise FormValuesError("End date must be after end date!", "RegistrationForm")
            regForm.setStartRegistrationDate(sDate)
            regForm.setEndRegistrationDate(eDate)
            regForm.setEndExtraTimeAmount(self._extraTimeAmount)
            regForm.setEndExtraTimeUnit(self._extraTimeUnit)
            regForm.setModificationEndDate(meDate)
            regForm.setAnnouncement(params["announcement"])
            regForm.setTitle( params["title"] )
            regForm.setContactInfo( params["contactInfo"] )
            regForm.setUsersLimit( params["usersLimit"] )
            regForm.getNotification().setToList( utils.getEmailList(params.get("toList", "")) )
            regForm.getNotification().setCCList( utils.getEmailList(params.get("ccList", "")) )
            regForm.setMandatoryAccount(params.has_key("mandatoryAccount"))
            regForm.setNotificationSender(params["notificationSender"])
            regForm.setSendRegEmail(params.has_key("sendRegEmail"))
            regForm.setSendReceiptEmail(params.has_key("sendReceiptEmail"))
            regForm.setSendPaidEmail(params.has_key("sendPaidEmail"))
        self._redirect(urlHandlers.UHConfModifRegForm.getURL(self._conf))

class RHRegistrationFormActionStatuses( RHRegistrationFormModifBase ):

    def _checkParams( self, params ):
        RHRegistrationFormModifBase._checkParams( self, params )
        self._action=None
        if params.has_key("addStatus"):
            self._action=_ActionNewStatus(self, self._conf, params)
        if params.has_key("removeStatuses"):
            self._action=_ActionRemoveStatuses(self, self._conf, params)

    def _process( self ):
        if self._action is not None:
            r=self._action.perform()
            if r is not None:
                return r
        self._redirect("%s#statuses"%urlHandlers.UHConfModifRegForm.getURL(self._conf))

class _ActionNewStatus:

    def __init__(self, rh, conf, params):
        self._rh=rh
        self._conf=conf
        self._params=params

    def perform( self ):
        if self._params.get("caption","").strip() !="":
            self._conf.getRegistrationForm().addStatus(Status(self._conf.getRegistrationForm(), self._params))

class _ActionRemoveStatuses:

    def __init__(self, rh, conf, params):
        self._conf=conf
        self._rh=rh
        self._params=params

    def _checkParams( self, params ):
        RHRegistrationFormModifBase._checkParams( self._rh, params )
        self._confirm = params.has_key( "confirm" )
        self._cancel = params.has_key("cancel")
        self.statusesIds=self._rh._normaliseListParam(params.get("statusesIds",[]))
        self._statuses = []
        for id in self.statusesIds:
            self._statuses.append(self._conf.getRegistrationForm().getStatusById(id))

    def perform( self ):
        self._checkParams(self._params)
        if not self._cancel and self._statuses!=[]:
            if self._confirm:
                for st in self._statuses:
                    self._conf.getRegistrationForm().removeStatus(st)
            else:
                return registrationForm.WPConfModifRegFormStatusesRemConfirm( self._rh, self._conf, self.statusesIds).display()

class RHRegistrationFormModifStatusBase( RHRegistrationFormModifBase ):

    def _checkParams(self, params):
        RHRegistrationFormModifBase._checkParams( self, params )
        self._status=self._conf.getRegistrationForm().getStatusById(params.get("statusId",""))

class _TmpStatus:

    def __init__(self, params, status=None):
        self._id=""
        self._caption=""
        self._counter=0
        self._values=[]
        self._defaultValue=None
        if status is not None:
            self._caption=status.getCaption()
            for sv in status.getStatusValuesList():
                nsv=sv.clone(self)
                nsv.setId(sv.getId())
                self._values.append(nsv)
            self._defaultValue=status.getDefaultValue()
        else:
            self.map(params)

    def getValues(self):
        d={}
        d['caption']=self.getCaption()
        d['values']=[]
        for v in self._values:
            d['values'].append({'id':v.getId(),'caption':v.getCaption()})
        d["defaultvalue"]=""
        if self._defaultValue is not None:
            d["defaultvalue"]=self._defaultValue.getId()
        return d

    def map(self, params):
        self._caption=params.get("caption","")
        if params.get("addvalue","").strip()!="":
            sv=StatusValue(self)
            cap=params.get("newvalue")
            if cap.strip()!="":
                sv.setCaption(params.get("newvalue"))
                sv.setId("t%s"%self._counter)
                self._counter+=1
                self._values.append(sv)
        elif params.get("removevalue","").strip()!="":
            vs=params.get("valuesIds",[])
            if type(vs)!=list:
                vs=[vs]
            for id in vs:
                self.removeValueById(id)
        elif params.get("defaultvalue","").strip()!="":
            vs=params.get("valuesIds",[])
            if type(vs)!=list:
                vs=[vs]
            if len(vs) == 1:
                v=self.getValueById(vs[0])
                self._defaultValue=v

    def getValueById(self, id):
        for v in self._values:
            if v.getId()==id:
                return v
        return None

    def removeValueById(self, id):
        for v in self._values:
            if v.getId()==id:
                self._values.remove(v)
                if v == self._defaultValue:
                    self._defaultValue=None
                return

    def getCaption(self):
        return self._caption

    def setCaption(self,c):
        self._caption=c

    def getDefaultValue(self):
        return self._defaultValue

    def getStatusValuesList(self, sort=False):
        r=self._values
        if sort:
            r.sort(StatusValue._cmpCaption)
        return r

class RHRegistrationFormStatusModif( RHRegistrationFormModifStatusBase ):

    def _checkParams(self, params):
        RHRegistrationFormModifStatusBase._checkParams(self, params)
        self._firstTime=params.get('firstTime','yes')!='no'

    def _process(self):
        if self._firstTime:
            session.pop('tmpStatus', None)
        tmpStatus = session.get('tmpStatus')
        if tmpStatus is None:
            tmpStatus = _TmpStatus(self._getRequestParams(), self._status)
        session['tmpStatus'] = tmpStatus
        p = registrationForm.WPConfModifRegFormStatusModif(self, self._status, tmpStatus)
        return p.display()

class RHRegistrationFormModifStatusPerformModif( RHRegistrationFormModifStatusBase ):

    def _checkParams( self, params ):
        RHRegistrationFormModifStatusBase._checkParams( self, params )
        self._cancel = params.has_key("cancel")
        self._save = params.has_key("save")

    def _process( self ):
        if not self._cancel:
            # setup the server variable with the values for the section field
            tmpStatus = session.get('tmpStatus')
            if tmpStatus is None:
                raise MaKaCError(_("Error trying to modify the status"))
            else:
                tmpStatus.map(self._getRequestParams())
            session['tmpStatus'] = tmpStatus
            #-----
            if self._save:
                self._status.setValues(tmpStatus.getValues())
                session.pop('tmpStatus', None)
            else:
                urlModif=urlHandlers.UHConfModifRegFormStatusModif.getURL(self._status)
                urlModif.addParam("firstTime", "no")
                self._redirect(urlModif)
                return
        else:
            session.pop('tmpStatus', None)
        self._redirect("%s#statuses"%urlHandlers.UHConfModifRegForm.getURL(self._conf.getRegistrationForm()))

