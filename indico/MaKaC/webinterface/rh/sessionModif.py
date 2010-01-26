# -*- coding: utf-8 -*-
##
## $Id: sessionModif.py,v 1.75 2009/06/19 14:38:44 pferreir Exp $
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
from MaKaC.errors import MaKaCError, FormValuesError
import MaKaC.webinterface.pages.errors as errors
import MaKaC.common.filters as filters
import MaKaC.webinterface.common.contribFilters as contribFilters
from MaKaC.webinterface.common.contribStatusWrapper import ContribStatusList
from MaKaC.webinterface.common.slotDataWrapper import Slot
from MaKaC.PDFinterface.conference import ConfManagerContribsToPDF
from MaKaC.common import Config
from BTrees.OOBTree import OOBTree
from BTrees.IOBTree import IOBTree
from sets import Set
from datetime import datetime,timedelta,date
from MaKaC.errors import FormValuesError
from MaKaC.conference import SessionChair
from MaKaC.i18n import _
from pytz import timezone

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
        if self._target.canCoordinate(self.getAW()):
            return
        RHSessionModifBase._checkProtection( self )

class RHSessionModUnrestrictedTTCoordinationBase(RHSessionModifBase):

    def _checkProtection(self):
        if self._target.canCoordinate(self.getAW(), "unrestrictedSessionTT"):
            return
        RHSessionModifBase._checkProtection( self )

class RHSessionModUnrestrictedContribMngCoordBase(RHSessionModifBase):

    def _checkProtection(self):
        if self._target.canCoordinate(self.getAW(), "modifContribs"):
            return
        RHSessionModifBase._checkProtection( self )

class RHSessionModification(RHSessionModCoordinationBase):
    _uh = urlHandlers.UHSessionModification

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

class RHSessionDatesModification(RHSessionModifBase):
    _uh=urlHandlers.UHSessionDatesModification

    def _checkParams(self,params):
        self._check = int(params.get("check",1))
        self._slmove = int(params.get("slmove",1))
        RHSessionModifBase._checkParams(self,params)
        self._confirmed=params.has_key("confirm")
        self._action=""
        if params.has_key("CANCEL") or params.has_key("cancel"):
            self._action="CANCEL"
        elif params.has_key("OK") or params.has_key("confirm"):
            self._action="MODIFY"
        elif params.has_key("performedAction") :
            self._action=params["performedAction"]                    
        else:
            sd,ed=self._session.getAdjustedStartDate(),self._session.getAdjustedEndDate()
            params["sYear"],params["sMonth"]=sd.year,sd.month
            params["sDay"]=sd.day
            params["sHour"],params["sMinute"]=sd.hour,sd.minute
            params["eYear"],params["eMonth"]=ed.year,ed.month
            params["eDay"]=ed.day
            params["eHour"],params["eMinute"]=ed.hour,ed.minute

    def _modify(self,params):
        tz = self._session.getConference().getTimezone()
        sd = timezone(tz).localize(datetime( int( params["sYear"] ), \
                                             int( params["sMonth"] ), \
                                             int( params["sDay"] ), \
                                             int( params["sHour"] ), \
                                             int( params["sMinute"] )))
        params["sDate"]=sd.astimezone(timezone('UTC'))
        if params.get("eYear","") == "":
           ed = timezone(tz).localize(datetime( int( params["sYear"] ), 
                                                int( params["sMonth"] ), \
                                                int( params["sDay"] ), \
                                                int( params["eHour"] ), \
                                                int( params["eMinute"] )))
        else:
           ed = timezone(tz).localize(datetime( int( params["eYear"] ), 
                                                int( params["eMonth"] ), \
                                                int( params["eDay"] ), \
                                                int( params["eHour"] ), \
                                                int( params["eMinute"] )))
        params["eDate"] = ed.astimezone(timezone('UTC'))
        self._target.setDates(params["sDate"],params["eDate"],self._check,self._slmove)
    
    def _getErrors(self,params):
        l=[]
        title=str(params.get("title",""))
        if title.strip()=="":
            l.append( _("session title cannot be empty"))
        return l
    
    def _process( self ):
        url=urlHandlers.UHSessionModifSchedule.getURL(self._target)
        params=self._getRequestParams()
        errorList = []
        if self._action=="CANCEL":
            self._redirect(url)
            return
        elif self._action=="MODIFY":
            self._modify(params)
            self._redirect(url)
            return
        p=sessions.WPSessionDatesModification(self,self._target)
        params=self._getRequestParams()
        params["errors"]=errorList
        return p.display(**params)

    def _getPreservedParams(self):
        params = self._websession.getVar("preservedParams")
        if params is None :
            return {}
        return params
    
    def _preserveParams(self, params):
        self._websession.setVar("preservedParams",params)
    
    def _removePreservedParams(self):
        self._websession.setVar("preservedParams",None)    
        
class RHSessionDataModification( RoomBookingDBMixin, RHSessionModifBase ):
    _uh=urlHandlers.UHSessionDataModification

    def _checkParams(self,params):
        self._check = int(params.get("check",1))
        self._slmove = int(params.get("slmove",0))
        RHSessionModifBase._checkParams(self,params)
        self._confirmed=params.has_key("confirm")
        self._action=""
        if params.has_key("CANCEL") or params.has_key("cancel"):
            self._action="CANCEL"
        elif params.has_key("OK") or params.has_key("confirm"):
            self._action="MODIFY"
        elif params.has_key("performedAction") :
            self._action=params["performedAction"]                    
        else:
            params["title"]=self._session.getTitle()
            params["code"]=self._session.getCode()
            params["description"]=self._session.getDescription()
            tz = self._session.getConference().getTimezone()
            sd=self._session.getStartDate().astimezone(timezone(tz))
            ed=self._session.getEndDate().astimezone(timezone(tz))
            params["sYear"],params["sMonth"]=sd.year,sd.month
            params["sDay"]=sd.day
            params["sHour"],params["sMinute"]=sd.hour,sd.minute
            params["eYear"],params["eMonth"]=ed.year,ed.month
            params["eDay"]=ed.day
            params["eHour"],params["eMinute"]=ed.hour,ed.minute
            cdur=self._session.getContribDuration()
            params["durHour"],params["durMin"]=int(cdur.seconds/3600),int((cdur.seconds % 3600)/60)
            params["tt_type"]=self._session.getScheduleType()
        
        self._evt = self._session

    def _getErrors(self,params):
        l=[]
        title=str(params.get("title",""))
        if title.strip()=="":
            l.append("session title cannot be empty")
        return l

    def _modify(self,params):
        tz = self._conf.getTimezone()
        sd = timezone(tz).localize(datetime( int( params["sYear"] ), \
                                                        int( params["sMonth"] ), \
                                                        int( params["sDay"] ), \
                                                        int( params["sHour"] ), \
                                                        int( params["sMinute"] )))
        params["sDate"] = sd.astimezone(timezone('UTC'))
        if params.get("eYear","") == "":
            ed = timezone(tz).localize(datetime( int( params["sYear"] ), \
                                    int( params["sMonth"] ), \
                                    int( params["sDay"] ), \
                                    int( params["eHour"] ), \
                                    int( params["eMinute"] )))
        else:
            ed = timezone(tz).localize(datetime( int( params["eYear"] ), \
                                    int( params["eMonth"] ), \
                                    int( params["eDay"] ), \
                                    int( params["eHour"] ), \
                                    int( params["eMinute"] )))
        params["eDate"] = ed.astimezone(timezone('UTC'))
        self._target.setValues(params,self._check,self._slmove, True)
        self._target.setScheduleType(params.get("tt_type",self._target.getScheduleType()))
    
    def _process( self ):
        errorList=[]
        url=urlHandlers.UHSessionModification.getURL(self._target)
        params=self._getRequestParams()
        if self._action=="CANCEL":
            self._redirect(url)
            return
        elif self._action=="MODIFY":
            errorList=self._getErrors(self._getRequestParams())
            if len(errorList)==0:
                newSchType=params.get("tt_type",self._target.getScheduleType())
                if self._target.getScheduleType()!=newSchType and\
                        not self._confirmed:
                    p=sessions.WPModEditDataConfirmation(self,self._target)
                    del params["confId"]
                    del params["sessionId"]
                    del params["OK"]
                    return p.display(**params)
                self._modify(params)
                self._redirect(url)
                return 
        elif self._action == "New convener" :
            self._preserveParams(params)            
            url = urlHandlers.UHSessionDataModificationConvenerSearch.getURL(self._conf)
            url.addParam("sessionId",self._session.getId())
            
            self._redirect(url)
        elif self._action == "Remove conveners" :
            self._removePersons(params, "convener")
        elif self._action == "Add convener" :
            self._preserveParams(params)
            url = urlHandlers.UHSessionDataModificationPersonAdd.getURL(self._conf)
            url.addParam("sessionId",self._session.getId())
            url.addParam("orgin","added")
            url.addParam("typeName","convener")
            self._redirect(url)   
        p=sessions.WPSessionDataModification(self,self._target)
        wf = self.getWebFactory()
        if wf != None:
            p = wf.getSessionDataModification(self,self._target)
        params=self._getRequestParams()
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
        """
        List of persons is indexed by their ID in the apropriate 
        list in session
        """        
        list = None
        if typeName == "convener" :
            list = self._session.getConvenerList()
        
        for p in persons :
            perspntoRemove = None
            if typeName == "convener" :
                personToRemove = self._session.getConvenerById(p)
            list.remove(personToRemove)
            
#-------------------------------------------------------------------------------------

class RHSessionDataModificationConvenerSearch( RHSessionModifBase):
    _uh = urlHandlers.UHSessionDataModificationConvenerSearch

    def _checkParams( self, params):
        RHSessionModifBase._checkParams(self,params)
        
    def _process( self ):
        params = self._getRequestParams()
        
        params["newButtonAction"] = str(urlHandlers.UHSessionDataModificationConvenerNew.getURL())
        
        addURL = urlHandlers.UHSessionDataModificationPersonAdd.getURL()
        addURL.addParam("orgin","selected")
        addURL.addParam("typeName","convener")
        params["addURL"] = addURL
        p = sessions.WPSessionDataModificationConvenerSelect( self, self._target)
        return p.display(**params)

#-------------------------------------------------------------------------------------

class RHSessionDataModificationConvenerNew( RHSessionModifBase ):
    _uh = urlHandlers.UHSessionDataModificationConvenerNew

    def _checkParams( self, params):
        RHSessionModifBase._checkParams(self,params)
        
    def _process( self ):
        p = sessions.WPSessionDataModificationConvenerNew( self, self._target)
        return p.display()

#-------------------------------------------------------------------------------------

class RHSessionDataModificationPersonAdd( RHSessionModifBase ):
    _uh = urlHandlers.UHSessionDataModificationPersonAdd

    def _checkParams( self, params):
        RHSessionModifBase._checkParams(self,params)
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
                url = urlHandlers.UHSessionDataModification.getURL(self._conf)
                url.addParam("sessionId",self._session.getId())
                self._redirect(url)
                return
            else :
                person = SessionChair()
                person.setFirstName(params["name"])
                person.setFamilyName(params["surName"])
                person.setEmail(params["email"])
                person.setAffiliation(params["affiliation"])
                person.setAddress(params["address"])
                person.setPhone(params["phone"])
                person.setTitle(params["title"])
                person.setFax(params["fax"])                
                if not self._alreadyDefined(person, self._typeName) :
                    self._session.addConvener(person)
                    if params.has_key("submissionControl") :
                        self._session.grantSubmission(person)
                else :
                    self._errorList.append("%s has been already defined as %s of this session"%(person.getFullName(),self._typeName))
        
        elif params.get("orgin","") == "selected" :
            selectedList = self._normaliseListParam(self._getRequestParams().get("selectedPrincipals",[]))
            
            for s in selectedList :
                if s[0:8] == "*author*" :
                    auths = self._conf.getAuthorIndex()
                    selected = auths.getById(s)
                else :
                    ph = user.PrincipalHolder()
                    selected = ph.getById(s)                            
                if isinstance(selected, user.Avatar) :
                    person = SessionChair()
                    person.setDataFromAvatar(selected)                    
                    if not self._alreadyDefined(person, self._typeName) :
                        self._session.addConvener(person)
                        if params.has_key("submissionControl") :
                            self._session.grantSubmission(person)
                    else :
                        self._errorList.append("%s has been already defined as %s of this session"%(person.getFullName(),self._typeName))
                        
                elif isinstance(selected, user.Group) : 
                    for member in selected.getMemberList() :
                        person = SessionChair()
                        person.setDataFromAvatar(member)
                        if not self._alreadyDefined(person, self._typeName) :
                            self._session.addConvener(person)
                            if params.has_key("submissionControl") :
                                self._session.grantSubmission(person)
                        else :
                            self._errorList.append("%s has been already defined as %s of this session"%(presenter.getFullName(),self._typeName))
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
                    if not self._alreadyDefined(person, self._typeName) :
                        self._session.addConvener(person)
                        if params.has_key("submissionControl") :
                            self._session.grantSubmission(person)
                    else :
                        self._errorList.append("%s has been already defined as %s of this session"%(person.getFullName(),self._typeName))
                
        elif params.get("orgin","") == "added" :
            preservedParams = self._getPreservedParams()
            chosen = preservedParams.get("%sChosen"%self._typeName,None)
            if chosen is None or chosen == "" : 
                url = urlHandlers.UHSessionDataModification.getURL(self._conf)
                url.addParam("sessionId",self._session.getId())
                self._redirect(url)
                return            
            index = chosen.find("-")
            objectId = chosen[1:index]
            chosenId = chosen[index+1:len(chosen)]
            if chosen[0:1] == "d" :                
                object = self._conf.getSessionById(objectId)
            else :
                object = self._conf.getContributionById(objectId)
            chosenPerson = None
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
            if not self._alreadyDefined(person, self._typeName) :
                self._session.addConvener(person)
                if params.has_key("submissionControl") :
                    self._session.grantSubmission(person)
            else :
                self._errorList.append("%s has been already defined as %s of this session"%(person.getFullName(),self._typeName))
        else :
            url = urlHandlers.UHSessionDataModification.getURL(self._conf)
            url.addParam("sessionId",self._session.getId())
            self._redirect(url)
            return
        preservedParams = self._getPreservedParams()
        preservedParams["errorMsg"] = self._errorList
        self._preserveParams(preservedParams)
        self._websession.setVar("%sList"%self._typeName,definedList)
        
        url = urlHandlers.UHSessionDataModification.getURL(self._conf)
        url.addParam("sessionId",self._session.getId())
        self._redirect(url)


    def _getDefinedList(self, typeName):
        definedList = self._websession.getVar("%sList"%typeName)
        if definedList is None :
            return []
        return definedList
        
    def _alreadyDefined(self, person, typeName):
        if person is None :
            return True
        if typeName is None :
            return True
        fullName = person.getFullName()
        list = None
        if typeName == "convener" :
            list = self._session.getConvenerList()
        for p in list :
            if p.getFullName() == fullName :
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

class RHSessionDataModificationNewConvenerCreate( RHSessionModifBase ):
    _uh = urlHandlers.UHSessionDataModificationNewConvenerCreate

    def _checkParams( self, params):
        RHSessionModifBase._checkParams(self,params)
        
    def _process( self ):
        
        params = self._getRequestParams()
        formAction = urlHandlers.UHSessionDataModificationConvenerAdd.getURL(self._conf)
        formAction.addParam("sessionId",self._session.getId())
        formAction.addParam("orgin","new")
        formAction.addParam("typeName","convener")
        params["formAction"] = formAction
        p = sessions.WPSessionDataModificationConvenerNew( self, self._target)
        return p.display(**params)

#-------------------------------------------------------------------------------------

class RHSessionDataModificationNewConvenerSearch( RHSessionModifBase):
    _uh = urlHandlers.UHSessionDataModificationNewConvenerSearch

    def _checkParams( self, params):
        RHSessionModifBase._checkParams(self,params)
        
    def _process( self ):
        params = self._getRequestParams()
        
        params["newButtonAction"] = str(urlHandlers.UHSessionDataModificationNewConvenerCreate.getURL())
        addURL = urlHandlers.UHSessionDataModificationConvenerAdd.getURL()
        addURL.addParam("orgin","selected")
        addURL.addParam("typeName","convener")
        params["addURL"] = addURL
        p = sessions.WPSessionDataModificationConvenerSelect( self, self._target)
        return p.display(**params)

#-------------------------------------------------------------------------------------

class RHSessionDataModificationConvenerAdd( RHSessionModifBase ):
    _uh = urlHandlers.UHSessionDataModificationConvenerAdd

    def _checkParams( self, params):
        RHSessionModifBase._checkParams(self,params)
        self._typeName = params.get("typeName",None)
        if self._typeName  is None :
            raise MaKaCError( _("Type name of the person to add is not set."))
        
    def _process( self ):
        params = self._getRequestParams()        
        self._errorList = []        
    
        if params.get("orgin","") == "new" :
            if params.get("ok",None) is None :                
                url = urlHandlers.UHSessionModification.getURL(self._conf)
                url.addParam("sessionId",self._session.getId())
                self._redirect(url)
                return
            else :
                person = SessionChair()
                person.setFirstName(params["name"])
                person.setFamilyName(params["surName"])
                person.setEmail(params["email"])
                person.setAffiliation(params["affiliation"])
                person.setAddress(params["address"])
                person.setPhone(params["phone"])
                person.setTitle(params["title"])
                person.setFax(params["fax"])                
    
                self._session.addConvener(person)
                if params.has_key("coordinatorControl") :
                    self._session.addCoordinator(person)
                if params.has_key("managerControl") :
                    self._session.grantModification(person)
            
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
                    self._session.addConvener(person)
                    if params.has_key("coordinatorControl") :
                        self._session.addCoordinator(person)
                    if params.has_key("managerControl") :
                        self._session.grantModification(person)
                        
                elif isinstance(selected, user.Group) : 
                    for member in selected.getMemberList() :
                        person = SessionChair()
                        person.setDataFromAvatar(member)
                        self._session.addConvener(person)
                        if params.has_key("coordinatorControl") :
                            self._session.addCoordinator(person)
                        if params.has_key("managerControl") :
                            self._session.grantModification(person)
                        
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
                    self._session.addConvener(person)
                    if params.has_key("coordinatorControl") :
                        self._session.addCoordinator(person)
                    if params.has_key("managerControl") :
                        self._session.grantModification(person)
                            
        else :
            url = urlHandlers.UHSessionModification.getURL(self._conf)
            url.addParam("sessionId",self._session.getId())
            self._redirect(url)
            return
        
        url = urlHandlers.UHSessionModification.getURL(self._conf)
        url.addParam("sessionId",self._session.getId())
        self._redirect(url)


#-------------------------------------------------------------------------------------

class RHSessionClose( RHSessionModifBase ):
    _uh = urlHandlers.UHSessionClose
    
    def _process( self ):
        self._target.setClosed(True)
        self._redirect(urlHandlers.UHSessionModification.getURL(self._target))

class RHSessionOpen( RHSessionModifBase ):
    _uh = urlHandlers.UHSessionOpen
    
    def _process( self ):
        self._target.setClosed(False)
        self._redirect(urlHandlers.UHSessionModification.getURL(self._target))

class RHConvenerNew(RHSessionModifBase):
    _uh=urlHandlers.UHSessionModConvenerNew
    
    def _checkParams(self, params):
        RHSessionModifBase._checkParams(self,params)
        self._action=""
        if params.has_key("ok"):
            self._action = "perform"
        elif params.has_key("cancel"):
            self._action = "cancel"

    def _newConvener(self):
        c=conference.SessionChair()
        p=self._getRequestParams()
        c.setTitle(p.get("title",""))
        c.setFirstName(p.get("name",""))
        c.setFamilyName(p.get("surName",""))
        c.setAffiliation(p.get("affiliation",""))
        c.setEmail(p.get("email",""))
        c.setAddress(p.get("address",""))
        c.setPhone(p.get("phone",""))
        c.setFax(p.get("fax",""))
        self._target.addConvener(c)
        return c
    
    def _process(self):
        if self._action!="":
            if self._action=="perform":
                conv=self._newConvener()
                sr=self._getRequestParams().get("specialRights","none")
                if sr in ["manager","coordinator"]:
                    if self._getRequestParams().get("email","").strip() == "":
                        raise FormValuesError("If you want to add specific righst to this convener, please enter their email")
                    if sr == "manager":
                        self._target.grantModification(conv)
                    elif sr == "coordinator":
                        self._target.addCoordinator(conv)
            url=urlHandlers.UHSessionModification.getURL(self._target)
            self._redirect(url)
        else:
            p=sessions.WPModConvenerNew(self,self._session)
            wf = self.getWebFactory()
            if wf != None:
                p = wf.getModConvenerNew(self,self._session)
            return p.display(**self._getRequestParams())


class RHConvenersRem( RHSessionModifBase ):
    _uh = urlHandlers.UHSessionModConvenersRem
    
    def _checkParams( self, params ):
        RHSessionModifBase._checkParams( self, params )
        self._conv=[]
        for id in self._normaliseListParam(params.get("selConv",[])):
            self._conv.append(self._target.getConvenerById(id))
    
    def _process( self ):
        for conv in self._conv:
            self._session.removeConvener(conv)
        self._redirect(urlHandlers.UHSessionModification.getURL(self._session))


class RHConvenerEdit(RHSessionModifBase):
    
    def _checkParams(self,params):
        RHSessionModifBase._checkParams(self, params)
        self._convId=params["convId"]
        self._action=""
        if params.has_key("ok"):
            self._action = "perform"
        elif params.has_key("cancel"):
            self._action = "cancel"

    def _setConvenerData(self):
        c=self._target.getConvenerById(self._convId)
        p = self._getRequestParams()
        c.setTitle(p.get("title",""))
        c.setFirstName(p.get("name",""))
        c.setFamilyName(p.get("surName",""))
        c.setAffiliation(p.get("affiliation",""))
        c.setAddress(p.get("address",""))
        c.setPhone(p.get("phone",""))
        c.setFax(p.get("fax",""))
        
        c.setEmail(p.get("email",""))
        
        if p.get("coordinatorControl", None):
            self._target.addCoordinator(c)
        if p.get("managerControl", None):
            self._target.grantModification(c)

##        grant=0
##        if c.getEmail().lower().strip() != p.get("email","").lower().strip():
##            #----If it's already in the pending queue in order to grant 
##            #    modification/coordination rights we must unindex and after the modification of the email,
##            #    index again...
##            if self._target.getConference().getPendingQueuesMgr().isPendingManager(c):
##                self._target.getConference().getPendingQueuesMgr().removePendingManager(c)
##                grant=1
##            if self._target.getConference().getPendingQueuesMgr().isPendingCoordinator(c):
##                self._target.getConference().getPendingQueuesMgr().removePendingCoordinator(c)
##                grant=2
##            #-----
            
##        c.setEmail(p.get("email",""))
##        
##        if grant==1:
##            self._target.grantModification(c)
##        if grant==2:
##            self._target.addCoordinator(c)
        
    
    def _process(self):
        if self._action != "":
            if self._action == "perform":
                self._setConvenerData()
            url=urlHandlers.UHSessionModification.getURL(self._target)
            self._redirect(url)
        else:
            c=self._target.getConvenerById(self._convId)
            p=sessions.WPModConvenerEdit(self,self._target)
            wf = self.getWebFactory()
            if wf != None:
                p = wf.getModConvenerEdit(self, self._target)
            return p.display(convener=c)


class RHSessionAddMaterial( RHSessionModifBase ):
    _uh = urlHandlers.UHSessionAddMaterial
    
    def _checkParams( self, params ):
        RHSessionModifBase._checkParams( self, params )
        typeMat = params.get( "typeMaterial", "notype" )
        if typeMat=="notype" or typeMat.strip()=="":
            raise FormValuesError("Please choose a material type")
        self._mf = materialFactories.SessionMFRegistry().getById( typeMat )
        
    def _process( self ):
        if self._mf:
            if not self._mf.needsCreationPage():
                m = RHSessionPerformAddMaterial.create( self._session, self._mf, self._getRequestParams() )
                self._redirect( urlHandlers.UHMaterialModification.getURL( m ) )
                return
        p = sessions.WPSessionAddMaterial( self, self._session, self._mf )
        wf = self.getWebFactory()
        if wf != None:
            p = wf.getSessionAddMaterial(self,self._session, self._mf)
        return p.display()


class RHSessionPerformAddMaterial( RHSessionModifBase ):
    _uh = urlHandlers.UHSessionPerformAddMaterial
    
    def _checkParams( self, params ):
        RHSessionModifBase._checkParams( self, params )
        typeMat = params.get( "typeMaterial", "" )
        self._mf = materialFactories.SessionMFRegistry().getById( typeMat )

    def create( session, matFactory, matData ):
        if matFactory:
            m = matFactory.create( session )
        else:
            m = conference.Material()
            session.addMaterial( m )
            m.setValues( matData )
        return m
    create = staticmethod( create )

    def _process( self ):
        m = self.create( self._session, self._mf, self._getRequestParams() )
        self._redirect( urlHandlers.UHMaterialModification.getURL( m ) )


class RHSessionRemoveMaterials( RHSessionModifBase ):
    _uh = urlHandlers.UHSessionRemoveMaterials
    
    def _checkParams( self, params ):
        RHSessionModifBase._checkParams( self, params )
        typeMat = params.get( "typeMaterial", "" )
        self._materialIds = self._normaliseListParam( params.get("materialId", []) )
        self._returnURL = params.get("returnURL","")
    
    def _process( self ):
        for id in self._materialIds:
            #Performing the deletion of special material types
            f = materialFactories.SessionMFRegistry().getById( id )
            if f:
                f.remove( self._session )
            else:
                #Performs the deletion of additional material types
                mat = self._target.getMaterialById( id )
                self._target.removeMaterial( mat )
        if self._returnURL != "":
            url = self._returnURL
        else:
            url = urlHandlers.UHSessionModifMaterials.getURL( self._session )
        self._redirect( url )


class RHMaterials(RHSessionModUnrestrictedContribMngCoordBase):
    _uh = urlHandlers.UHSessionModifMaterials
    
    def _checkParams(self, params):
        RHSessionModUnrestrictedContribMngCoordBase._checkParams(self, params)
        if not hasattr(self, "_rhSubmitMaterial"):
            self._rhSubmitMaterial=RHSubmitMaterialBase(self._target, self)
        self._rhSubmitMaterial._checkParams(params)
        params["days"] = params.get("day", "all")
        if params.get("day", None) is not None :
            del params["day"]
    
    def _process(self):
        if self._target.getOwner().isClosed():
            p = conferences.WPConferenceModificationClosed( self, self._target )
            return p.display()

        p = sessions.WPSessionModifMaterials( self, self._target )
        return p.display(**self._getRequestParams())
    
class RHMaterialsAdd(RHSessionModUnrestrictedContribMngCoordBase):
    _uh = urlHandlers.UHSessionModifMaterials
    
    def _checkParams(self, params):
        RHSessionModUnrestrictedContribMngCoordBase._checkParams(self, params)
        if not hasattr(self, "_rhSubmitMaterial"):
            self._rhSubmitMaterial=RHSubmitMaterialBase(self._target, self)
        self._rhSubmitMaterial._checkParams(params)
    
    def _process( self ):
        if self._target.isClosed():
            p = sessions.WPSessionModificationClosed( self, self._target )
        else:
            r=self._rhSubmitMaterial._process(self, self._getRequestParams())
        if r is None:
            self._redirect(self._uh.getURL(self._target))
        return r


class RHReducedSessionScheduleAction(RHSessionModCoordinationBase):
    _uh = urlHandlers.UHReducedSessionScheduleAction
        
    def _checkParams(self,params):
        RHSessionModCoordinationBase._checkParams(self,params)
        if "confId" not in params :
            raise MaKaCError( _("confId parameter value not set - cannot procede"))
        if "sessionId" not in params :
            raise MaKaCError( _("sessionId parameter value not set - cannot procede"))
        if "slotId" not in params :
            raise MaKaCError( _("slotId parameter value not set - cannot procede"))

    def _process( self ):
        if self._session.isClosed():
            p = sessions.WPSessionModificationClosed( self, self._session )
        else:
            params = self._getRequestParams()
            url = ""
            if "newContrib" in params :
                orginURL = urlHandlers.UHSessionModifSchedule.getURL(self._session.getOwner())
                orginURL.addParam("sessionId", self._session.getId())
                url = urlHandlers.UHConfModScheduleNewContrib.getURL(self._session.getOwner())
                url.addParam("sessionId", self._session.getId())
                url.addParam("orginURL",orginURL)
                url.addParam("eventType","meeting")
                url.addParam("slotId",params["slotId"])
                self._redirect(url)
            elif "newBreak" in params :
                url = urlHandlers.UHSessionAddBreak.getURL(self._session.getOwner())
                url.addParam("sessionId",params["sessionId"])
                url.addParam("slotId",params["slotId"])
                self._redirect(url)
            elif "reschedule" in params :
                url = urlHandlers.UHSessionModSlotCalc.getURL(self._session.getOwner())
                url.addParam("sessionId",params["sessionId"])
                url.addParam("slotId",params["slotId"])
                self._redirect(url)
            else :
                url = urlHandlers.UHSessionModifSchedule.getURL(self._session.getOwner())
                url.addParam("sessionId", self._session.getId())
                url.addParam("slotId",params["slotId"])
                self._redirect(url)
                


class RHSessionModifSchedule(RHSessionModCoordinationBase):
    _uh = urlHandlers.UHSessionModifSchedule
        
    def _checkParams(self,params):
        RHSessionModCoordinationBase._checkParams(self,params)
        if params.get("view","parallel").strip()!="":
            self._getSession().ScheduleView = params.get("view","parallel").strip()
        try:
            if self._getSession().ScheduleView:
                pass
        except AttributeError:
            self._getSession().ScheduleView=params.get("view","parallel")
        self._view=self._getSession().ScheduleView
        params["days"] = params.get("day", "all")
        if params.get("day", None) is not None :
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
        params['view'] = self._view
    
        return p.display(**params)


class RHScheduleAddContrib(RHSessionModCoordinationBase):
    _uh = urlHandlers.UHSessionModScheduleAddContrib
        
    def _checkParams(self,params):
        RHSessionModCoordinationBase._checkParams(self,params)
        self._slot=None
        if params.has_key("slotId"):
            self._slot=self._target.getSlotById(params["slotId"])
        else:
            raise MaKaCError( _("Slot ID is not specified"), _("Contribution Addition"))
        self._action=""
        if params.has_key("OK"):
            self._action="ADD"
            self._selContribIdList=params.get("selContribs","").split(",")
            self._selContribIdList+=self._normaliseListParam(params.get("manSelContribs",[]))
        elif params.has_key("CANCEL"):
            self._action="CANCEL"

    def _process( self ):
        if self._action=="ADD":
            for contribId in self._selContribIdList:
                if contribId.strip()=="":
                    continue
                contrib=self._target.getConference().getContributionById(contribId)
                if contrib is None:
                    continue
                if self._slot.getSession().getScheduleType() == "poster":
                    contrib.setStartDate(self._slot.getStartDate())
                schedule=self._slot.getSchedule()
                schedule.addEntry(contrib.getSchEntry())
            self._redirect(urlHandlers.UHSessionModifSchedule.getURL(self._target))
        elif self._action=="CANCEL":
            self._redirect(urlHandlers.UHSessionModifSchedule.getURL(self._target))
        p=sessions.WPModScheduleAddContrib(self,self._target)
        return p.display(slot=self._slot)


#class RHSessionAddContribution( RHSessionModifBase ):
#    pass


#class RHSessionPerformAddContribution( RHSessionModifBase ):
#    pass


class RHSessionAddBreak( RoomBookingDBMixin, RHSessionModCoordinationBase ):
    _uh = urlHandlers.UHSessionAddBreak
    
    def _checkParams( self, params ):
        self._check = int(params.get("check",1))
        RHSessionModifBase._checkParams( self, params )
        self._slot=self._target.getSlotById(params.get("slotId",""))
        self._action=""
        if params.has_key("CANCEL"):
            self._action="CANCEL"
        elif params.has_key("OK"):
            self._action="ADD"
        
        self._evt = None
        
    def _process( self ):
        if self._action=="CANCEL":
            self._redirect(urlHandlers.UHSessionModifSchedule.getURL(self._target))
        elif self._action=="ADD":
            params = self._getRequestParams()
            if params["locationAction"] == "inherit":
                params["locationName"] = ""
            if params["roomAction"] == "inherit":
                params["roomName"] = ""
            b=schedule.BreakTimeSchEntry()
            b.setValues(self._getRequestParams(), tz = self._conf.getTimezone())
            self._slot.getSchedule().addEntry(b,self._check)
            self._redirect(urlHandlers.UHSessionModifSchedule.getURL(self._target))
        else:
            p=sessions.WPSessionAddBreak(self,self._slot)
            wf = self.getWebFactory()
            if wf != None:
                p = wf.getSessionAddBreak(self,self._slot)
            return p.display()





class RHSessionDelSchItems(RHSessionModCoordinationBase):
    _uh = urlHandlers.UHSessionDelSchItems
    
    def _checkParams( self, params ):
        RHSessionModCoordinationBase._checkParams( self, params )
        self._slot=self._target.getSlotById(params.get("slotId",""))
        self._entries=[]
        for id in self._normaliseListParam(params.get("schEntryId",[])):
            entry=self._slot.getSchedule().getEntryById(id)
            if entry is not None:
                self._entries.append(entry)

    def _process( self ):
        type = self._conf.getType()
        for e in self._entries:
            if type == "meeting":                   
                logInfo = e.getOwner().getLogInfo()
                logInfo["subject"] = "Deleted contribution: %s"%e.getOwner().getTitle()
                self._conf.getLogHandler().logAction(logInfo,"Timetable/Contribution",self._getUser())
                if not isinstance(e, schedule.BreakTimeSchEntry):
                    e.getOwner().delete()
                self._slot.getSchedule().removeEntry(e)
            else:          
                logInfo = e.getOwner().getLogInfo()
                logInfo["subject"] = "Unscheduled contribution: %s"%e.getOwner().getTitle()
                self._conf.getLogHandler().logAction(logInfo,"Timetable/Contribution",self._getUser())
                self._slot.getSchedule().removeEntry(e)
        self._redirect(urlHandlers.UHSessionModifSchedule.getURL(self._session))

    
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
        privacy = params.get("visibility","PUBLIC")
        self._protect = 0
        if privacy == "PRIVATE":
            self._protect = 1
        elif privacy == "PUBLIC":
            self._protect = 0
        elif privacy == "ABSOLUTELY PUBLIC":
            self._protect = -1
            
    def _process( self ):
        self._session.setProtection( self._protect )
        self._redirect( urlHandlers.UHSessionModifAC.getURL( self._session ) )


class RHSessionSelectAllowed( RHSessionModifBase ):
    _uh = urlHandlers.UHSessionSelectAllowed
    
    def _process( self ):
        p = sessions.WPSessionSelectAllowed( self, self._session )
        return p.display( **self._getRequestParams() )


class RHSessionAddAllowed( RHSessionModifBase ):
    _uh = urlHandlers.UHSessionAddAllowed
    
    def _checkParams( self, params ):
        RHSessionModifBase._checkParams( self, params )
        selAllowedId = self._normaliseListParam( params.get( "selectedPrincipals", [] ) )
        #ah = user.AvatarHolder()
        ph = user.PrincipalHolder()
        self._allowed = []
        for id in selAllowedId:
            self._allowed.append( ph.getById( id ) )
    
    def _process( self ):
        for av in self._allowed:
            self._target.grantAccess( av )
        self._redirect( urlHandlers.UHSessionModifAC.getURL( self._session ) )


class RHSessionRemoveAllowed( RHSessionModifBase ):
    _uh = urlHandlers.UHSessionRemoveAllowed

    def _checkParams( self, params ):
        RHSessionModifBase._checkParams( self, params )
        selAllowedId = self._normaliseListParam( params.get( "selectedPrincipals", [] ) )
        #ah = user.AvatarHolder()
        ph = user.PrincipalHolder()
        self._allowed = []
        for id in selAllowedId:
            self._allowed.append( ph.getById( id ) )
    
    def _process( self ):
        for av in self._allowed:
            self._target.revokeAccess( av )
        self._redirect( urlHandlers.UHSessionModifAC.getURL( self._session ) )


class RHSessionAddDomains( RHSessionModifBase ):
    _uh = urlHandlers.UHSessionAddDomains
    
    def _process( self ):
        params = self._getRequestParams()
        if ("addDomain" in params) and (len(params["addDomain"])!=0):
            dh = domain.DomainHolder()
            for domId in self._normaliseListParam( params["addDomain"] ):
                self._target.requireDomain( dh.getById( domId ) )
        self._redirect( urlHandlers.UHSessionModifAC.getURL( self._target ) )


class RHSessionRemoveDomains( RHSessionModifBase ):
    _uh = urlHandlers.UHSessionRemoveDomains
    
    def _process( self ):
        params = self._getRequestParams()
        if ("selectedDomain" in params) and (len(params["selectedDomain"])!=0):
            dh = domain.DomainHolder()
            for domId in self._normaliseListParam( params["selectedDomain"] ):
                self._target.freeDomain( dh.getById( domId ) )
        self._redirect( urlHandlers.UHSessionModifAC.getURL( self._target ) )


class RHSessionSelectManagers( RHSessionModifBase ):
    _uh = urlHandlers.UHSessionSelectManagers
    
    def _process( self ):
        p = sessions.WPSessionSelectManagers( self, self._target )
        return p.display( **self._getRequestParams() )


class RHSessionAddManagers( RHSessionModifBase ):
    _uh = urlHandlers.UHSessionAddManagers

    def _checkParams(self, params):
        RHSessionModifBase._checkParams(self, params)
        self._managerRole=self._normaliseListParam(params.get("userRole", []))
    
    def _process( self ):
        params = self._getRequestParams()
        if "selectedPrincipals" in params:
            ph = user.PrincipalHolder()
            for id in self._normaliseListParam( params["selectedPrincipals"] ):
                av=ph.getById( id )
                self._target.grantModification( av )
                if self._managerRole!=[]:
                    conv=conference.SessionChair()
                    conv.setDataFromAvatar(av)
                    if "convener" in self._managerRole:
                        self._target.addConvener(conv)
        self._redirect( urlHandlers.UHSessionModifAC.getURL( self._target ) )


class RHSessionRemoveManagers( RHSessionModifBase ):
    _uh = urlHandlers.UHSessionRemoveManagers
    
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
        self._redirect( urlHandlers.UHSessionModifAC.getURL( self._target ) )


class RHCoordinatorsSel(RHSessionModifBase):
    _uh=urlHandlers.UHSessionModCoordinatorsSel
    
    def _process( self ):
        p=sessions.WPModCoordinatorsSel(self,self._target)
        return p.display(**self._getRequestParams())


class RHCoordinatorsAdd(RHSessionModifBase):
    _uh = urlHandlers.UHSessionModCoordinatorsAdd

    def _checkParams(self, params):
        RHSessionModifBase._checkParams(self, params)
        self._coordRole=self._normaliseListParam(params.get("userRole", []))
    
    def _process( self ):
        params=self._getRequestParams()
        if "selectedPrincipals" in params:
            ph=user.PrincipalHolder()
            for id in self._normaliseListParam( params["selectedPrincipals"] ):
                av=ph.getById( id )
                self._target.addCoordinator( av )
                if self._coordRole!=[]:
                    conv=conference.SessionChair()
                    conv.setDataFromAvatar(av)
                    if "convener" in self._coordRole:
                        self._target.addConvener(conv)
        self._redirect(urlHandlers.UHSessionModifAC.getURL(self._target))


class RHCoordinatorsRem(RHSessionModifBase):
    _uh=urlHandlers.UHSessionModCoordinatorsRem
    
    def _process( self ):
        params=self._getRequestParams()
        if ("selectedPrincipals" in params) and \
            (len(params["selectedPrincipals"])!=0):
            ph=user.PrincipalHolder()
            for id in self._normaliseListParam( params["selectedPrincipals"] ):
                av = ph.getById(id)
                if av:
                    self._target.removeCoordinator(av)
                else:
                    self._target.removeCoordinatorEmail(id)
        self._redirect(urlHandlers.UHSessionModifAC.getURL(self._target))

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


class RHSessionWriteMinutes( RHSessionModifBase ):
    _uh = urlHandlers.UHSessionWriteMinutes

    def _checkParams( self, params ):
        RHSessionModifBase._checkParams( self, params )
        self._cancel = params.has_key("cancel")
        self._save = params.has_key("OK")
        self._text = params.get("text", "")#.strip()

    def _process( self ):
        if self._cancel:
            self._redirect( urlHandlers.UHSessionModifTools.getURL( self._session ) )
        elif self._save:
            #if self._text!="":
                minutes = self._session.getMinutes()
                if not minutes:
                    minutes = self._session.createMinutes()
                minutes.setText( self._text )
                self._redirect( urlHandlers.UHSessionModifTools.getURL( self._session ) )
        else:
            p = sessions.WPSessionWriteMinutes( self, self._session )
            return p.display()

class RHFitSession(RHSessionModCoordinationBase):
    
    def _checkParams(self, params):
        RHSessionModCoordinationBase._checkParams(self, params)
    
    def _process(self):
        if self._target is not None:
            self._target.fit()
        self._redirect(urlHandlers.UHSessionModifSchedule.getURL(self._target))


class RHSlotNew( RoomBookingDBMixin, RHSessionModUnrestrictedTTCoordinationBase ):

    def _checkParams(self, params):
        self._check = int(params.get("check",1))
        RHSessionModifBase._checkParams(self, params)
        self._slotDate = params.get("slotDate","")
        self._action = ""
        if params.get("cancel", None) is not None:
            self._action = "cancel"
        elif params.get("OK", None) is not None:
            self._action = "submit"
        elif params.get("addConvener", None) is not None:
            self._action = "addConvener"
        elif params.get("remConveners", None) is not None:
            self._action = "remConveners"
        toNorm=["conv_id","conv_title", "conv_first_name",
            "conv_family_name","conv_affiliation", 
            "conv_email"]
        for k in toNorm:
            params[k]=self._normaliseListParam(params.get(k,[]))
            
        self._evt = None
      
        
    def _process(self):

        self._slotData = Slot()
        params = self._getRequestParams()
        params["session"]=self._session
        if self._action == "cancel":
            self._redirect(urlHandlers.UHSessionModifSchedule.getURL(self._session))
        elif self._action == "submit":
            self._slotData.setValues(params)
            errors = self._slotData.getErrors()
            if errors ==[]:
                slot=conference.SessionSlot(self._session)
                params["conveners"]=self._slotData.getConvenerList()
                params["sDate"]=self._slotData.getStartDate()
                params["eDate"]=self._slotData.getEndDate()
                slot.setValues( params,self._check )
                self._session.addSlot(slot)
                logInfo = slot.getLogInfo()
                logInfo["subject"] = "Create new slot: %s"%slot.getTitle()
                self._conf.getLogHandler().logAction(logInfo,"Timetable/Contribution",self._getUser())
                
                self._redirect( urlHandlers.UHSessionModifSchedule.getURL( slot ) )
            else:
                p = sessions.WPModSlotNew(self,self._slotData, errors)
                return p.display()
        elif self._action == "addConvener":
            self._slotData.setValues(params)
            self._slotData.newConvener()
            p = sessions.WPModSlotNew(self, self._slotData)
            return p.display()
        elif self._action == "remConveners":
            self._slotData.setValues(params)
            idList = self._normaliseListParam( params.get("sel_conv", []) )
            self._slotData.removeConveners( idList )
            p = sessions.WPModSlotNew(self, self._slotData)
            return p.display()
        else:
            dateTuple = re.compile("^(\d*)-(\d*)-(\d*)$").match(self._slotDate).groups()
            auxdate = timezone(self._conf.getTimezone()).localize(datetime(int(dateTuple[2]), int(dateTuple[1]), int(dateTuple[0])))
            sdate = self._session.getSchedule().getFirstFreeSlotOnDay(auxdate)
            edate = sdate + timedelta(hours=1)
            params["sDate"]=sdate
            params["eDate"]=edate
            if self._session.getContribDuration()!=None:
                params["contribDuration"] = self._session.getContribDuration()
            else:
                params["contribDuration"] = timedelta(hours=0,minutes=20)
            self._slotData.setValues(params)
            p = sessions.WPModSlotNew(self, self._slotData )
            return p.display()


class RHSlotRem(RHSessionModUnrestrictedTTCoordinationBase):
    
    def _checkParams(self, params):
        RHSessionModUnrestrictedTTCoordinationBase._checkParams(self, params)
        self._slotId=params.get("slotId","")
        self._confirmed=params.has_key("confirm")
        self._cancel=params.has_key("cancel")
    
    def _process(self):
        if not self._cancel:
            slot=self._session.getSlotById(self._slotId)
            if not self._confirmed:
                p=sessions.WPModSlotRemConfirmation(self,slot)
                wf = self.getWebFactory()
                if wf != None:
                    p = wf.getModSlotRemConfirmation(self,slot)
                return p.display()
            self._session.removeSlot(slot)
        self._redirect(urlHandlers.UHSessionModifSchedule.getURL(self._session))

class RHSlotCalc(RHSessionModCoordinationBase):
    
    def _checkParams(self, params):
        RHSessionModifBase._checkParams(self, params)
        self._slotId=params.get("slotId","")
        self._cancel=params.has_key("CANCEL")
        self._ok=params.has_key("OK")
        self._hour=params.get("hour","")
        self._minute=params.get("minute","")
        self._action=params.get("action","duration")
        if self._ok:
            if self._hour.strip() == "" or self._minute.strip() == "":
                raise MaKaCError( _("Please write the time with the format HH:MM. For instance, 00:05 to indicate 'O hours' and '5 minutes'"))
            try:
                if int(self._hour) or int(self._hour):
                    pass
            except ValueError, e:
                raise MaKaCError( _("Please write a number to specify the time HH:MM. For instance, 00:05 to indicate 'O hours' and '5 minutes'"))
    
    def _process(self):
        if not self._cancel:
            slot=self._target.getSlotById(self._slotId)
            if not self._ok:
                p=sessions.WPModSlotCalc(self,slot)
                return p.display()
            else:
                t=timedelta(hours=int(self._hour), minutes=int(self._minute))
                slot.recalculateTimes(self._action, t)
        self._redirect(urlHandlers.UHSessionModifSchedule.getURL(self._session))

class RHSlotEdit( RoomBookingDBMixin, RHSessionModUnrestrictedTTCoordinationBase ):

    def _checkParams(self, params):
        RHSessionModUnrestrictedTTCoordinationBase._checkParams(self, params)
        self._slot=self._target.getSlotById(params.get("slotId",""))
        self._check = int(params.get("check",1))
        self._move = int(params.get("move",0))
        self._action = ""
        if params.get("cancel", None) is not None:
            self._action = "cancel"
        elif params.get("OK", None) is not None:
            self._action = "submit"
        elif params.get("addConvener", None) is not None:
            self._action = "addConvener"
        elif params.get("remConveners", None) is not None:
            self._action = "remConveners"
        if params.get( "bookedRoomName" ):
            params["roomName"] = params["bookedRoomName"]
        toNorm=["conv_id","conv_title", "conv_first_name",
            "conv_family_name","conv_affiliation", 
            "conv_email"]
        for k in toNorm:
            params[k]=self._normaliseListParam(params.get(k,[]))
        
        self._evt = self._slot

    def _process(self):
        
        self._slotData = Slot()
        if self._action == "cancel":
            self._redirect(urlHandlers.UHSessionModifSchedule.getURL(self._slot.getSession(), slotId=self._slot.getId()))
        elif self._action == "submit":
            params = self._getRequestParams()
            
            params["id"]=self._slot.getId()
            params["session"]=self._slot.getSession()
            params["conf"]=self._slot.getConference()
            params["move"]=self._move

            self._slotData.setValues(params)
            sloterrors = self._slotData.getErrors()
            if sloterrors ==[]:
                params["conveners"]=self._slotData.getConvenerList()
                self._slot.setValues( params, self._check )
                self._redirect( '%s#slot%s' % (urlHandlers.UHConfModifSchedule.getURL( self._conf, session=self._slot.getSession().getId() ), self._slot.getId()) )
            else:
                p = sessions.WPModSlotEdit(self, self._slotData, sloterrors)
                return p.display()
        elif self._action == "addConvener":
            params = self._getRequestParams()
            params["id"]=self._slot.getId()
            params["session"]=self._slot.getSession()
            self._slotData.setValues(params)
            self._slotData.newConvener()
            p = sessions.WPModSlotEdit(self, self._slotData)
            return p.display()
        elif self._action == "remConveners":
            params = self._getRequestParams()
            params["id"]=self._slot.getId()
            params["session"]=self._slot.getSession()
            self._slotData.setValues(params)
            idList = self._normaliseListParam( params.get("sel_conv", []) )
            self._slotData.removeConveners( idList )
            p = sessions.WPModSlotEdit(self, self._slotData)
            return p.display()
        else:
            self._slotData.mapSlot(self._slot)
            wf = self.getWebFactory()
            p = sessions.WPModSlotEdit(self, self._slotData) 
            if wf != None:
                   p = wf.getModSlotEdit(self, self._slotData)
            return p.display()


class RHSlotCompact(RHSessionModCoordinationBase):
    
    def _checkParams(self, params):
        RHSessionModCoordinationBase._checkParams(self, params)
        self._slot=self._target.getSlotById(params.get("slotId",""))
    
    def _process(self):
        if self._slot is not None:
            self._slot.getSchedule().compact()
        self._redirect(urlHandlers.UHSessionModifSchedule.getURL(self._session))


class RHFitSlot(RHSessionModCoordinationBase):
    
    def _checkParams(self, params):
        RHSessionModCoordinationBase._checkParams(self, params)
        self._slot=self._target.getSlotById(params.get("slotId",""))
    
    def _process(self):
        if self._slot is not None:
            self._slot.fit()
        self._redirect(urlHandlers.UHSessionModifSchedule.getURL(self._session))


class RHSlotMoveUpEntry(RHSessionModCoordinationBase):
    
    def _checkParams(self, params):
        RHSessionModCoordinationBase._checkParams(self, params)
        self._slot=self._target.getSlotById(params.get("slotId",""))
        self._entry=self._slot.getSchedule().getEntryById(params.get("schEntryId",""))
    
    def _process(self):
        if self._slot is not None and self._entry is not None:
            self._slot.getSchedule().moveUpEntry(self._entry)
        self._redirect(urlHandlers.UHSessionModifSchedule.getURL(self._session))


class RHSlotMoveDownEntry(RHSessionModCoordinationBase):
    
    def _checkParams(self, params):
        RHSessionModCoordinationBase._checkParams(self, params)
        self._slot=self._target.getSlotById(params.get("slotId",""))
        self._entry=self._slot.getSchedule().getEntryById(params.get("schEntryId",""))
    
    def _process(self):
        if self._slot is not None and self._entry is not None:
            self._slot.getSchedule().moveDownEntry(self._entry)
        self._redirect(urlHandlers.UHSessionModifSchedule.getURL(self._session))


class RHSessionModifyBreak( RoomBookingDBMixin, RHSessionModCoordinationBase ):
    _uh=urlHandlers.UHSessionModifyBreak
    
    def _checkParams(self,params):
        RHSessionModCoordinationBase._checkParams(self,params)
        if params.get("schEntryId","").strip()=="": 
           raise Exception("schedule entry order number not set")
        self._slot=self._target.getSlotById(params.get("slotId",""))
        self._break=self._slot.getSchedule().getEntryById(params.get("schEntryId",""))
        
        self._evt = None

        params["days"] = params.get("day", "all")
        if params.get("day", None) is not None :
            del params["day"]

    def _process(self):
        p=sessions.WPSessionModifyBreak(self,self._session,self._break)
        return p.display(**self._getRequestParams())


class RHSessionPerformModifyBreak(RHSessionModCoordinationBase):
    _uh = urlHandlers.UHSessionPerformModifyBreak
    
    def _checkParams( self, params ):
        self._check = int(params.get("check",1))
        self._moveEntries = int(params.get("moveEntries",0))
        RHSessionModCoordinationBase._checkParams( self, params )
        if params.get( "schEntryId", "" ).strip() == "":
            raise Exception( _("schedule entry order number not set"))
        self._slot=self._target.getSlotById(params.get("slotId",""))
        self._break=self._slot.getSchedule().getEntryById(params.get("schEntryId",""))
    
    def _process( self ):
        params = self._getRequestParams()
        if "CANCEL" not in params:
            self._break.setValues( params, self._check, self._moveEntries, tz=self._conf.getTimezone() )
        self._redirect( urlHandlers.UHSessionModifSchedule.getURL( self._session ) )
        

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
        self._req = req
    
    def process(self, params):
        if params.has_key("REMOVE"):
            return RHRemContribs(self._req).process(params)
        elif params.has_key("PDF"):
            return RHContribsToPDF(self._req).process(params)
        elif params.has_key("AUTH"):
            return RHContribsParticipantList(self._req).process(params)
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

        


