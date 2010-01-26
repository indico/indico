# -*- coding: utf-8 -*-
##
## $Id: contribMod.py,v 1.71 2009/06/04 12:07:13 cangelov Exp $
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

import MaKaC.webinterface.locators as locators
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.materialFactories as materialFactories
import MaKaC.webinterface.pages.contributions as contributions
import MaKaC.conference as conference
import MaKaC.user as user
import MaKaC.domain as domain
import MaKaC.webinterface.webFactoryRegistry as webFactoryRegistry
from MaKaC.webinterface.rh.base import RHModificationBaseProtected
from MaKaC.common.xmlGen import XMLGen
from MaKaC.common.utils import parseDateTime
from MaKaC.common import Config
from MaKaC.webinterface.rh.conferenceBase import RHSubmitMaterialBase
from MaKaC.webinterface.rh.base import RoomBookingDBMixin
from MaKaC.PDFinterface.conference import ConfManagerContribToPDF
from MaKaC.errors import FormValuesError
from MaKaC.conference import SubContribParticipation
from MaKaC.errors import MaKaCError
from MaKaC.i18n import _
from MaKaC.webinterface.pages.conferences import WPConferenceModificationClosed

class RHContribModifBase(RHModificationBaseProtected):
    """ Base RH for contribution modification.
        Sets the _target (the contribution) and the _conf (the conference)
    """
    
    def _checkParams(self, params):
        l = locators.WebLocator()
        l.setContribution(params)
        self._target = l.getObject()
        self._conf = self._target.getConference()

    def getWebFactory(self):
        wr = webFactoryRegistry.WebFactoryRegistry()
        self._wf = wr.getFactory(self._target.getConference())
        return self._wf
    
class RCSessionCoordinator(object):
    @staticmethod
    def hasRights(request):
        """ Returns true if the user is a Session Coordinator
        """
        if request._target.getSession() != None:
            return request._target.getSession().canCoordinate(request.getAW(), "modifContribs")
        else:
            return False
        
class RCContributionPaperReviewingStaff(object):
    
    @staticmethod
    def hasRights(request):
        """ Returns true if the user is a PRM, or a Referee / Editor / Reviewer of the target contribution
        """
        user = request.getAW().getUser()
        confReview = request._target.getConference().getConfReview()
        confReviewChoice = confReview.getChoice()
        reviewManager = request._target.getReviewManager()
        return (confReview.isPaperReviewManager(user) or \
               (reviewManager.hasReferee() and reviewManager.isReferee(user)) or \
               ((confReviewChoice == 3 or confReviewChoice == 4) and reviewManager.hasEditor() and reviewManager.isEditor(user)) or \
               ((confReviewChoice == 2 or confReviewChoice == 4) and request._target.getReviewManager().isReviewer(user)))
        
class RCContributionReferee(object):
    @staticmethod
    def hasRights(request):
        """ Returns true if the user is a referee of the target contribution
        """ 
        user = request.getAW().getUser()
        reviewManager = request._target.getReviewManager()
        return reviewManager.hasReferee() and reviewManager.isReferee(user)
    
class RCContributionEditor(object):
    @staticmethod
    def hasRights(request):
        """ Returns true if the user is an editor of the target contribution
        """ 

        user = request.getAW().getUser()
        reviewManager = request._target.getReviewManager()
        return reviewManager.hasEditor() and reviewManager.isEditor(user)
    
class RCContributionReviewer(object):
    @staticmethod
    def hasRights(request):
        """ Returns true if the user is a reviewer of the target contribution
        """ 
        user = request.getAW().getUser()
        reviewManager = request._target.getReviewManager()
        return reviewManager.isReviewer(user)

class RHContribModifBaseSpecialSesCoordRights(RHContribModifBase):
    """ Base class for any RH where a Session Coordinator has the rights to perform the request
    """

    def _checkProtection(self):
        if not RCSessionCoordinator.hasRights(self):
            RHContribModifBase._checkProtection(self)
        
class RHContribModifBaseReviewingStaffRights(RHContribModifBase):
    """ Base class for any RH where a member of the Paper Reviewing staff
        (a PRM, or a Referee / Editor / Reviewer of the target contribution)
        has the rights to perform the request
    """

    def _checkProtection(self):
        if not RCContributionPaperReviewingStaff.hasRights(self):
            RHContribModifBase._checkProtection(self);
            
class RHContribModifBaseSpecialSesCoordAndReviewingStaffRights(RHContribModifBase):
    """ Base class for any RH where a member of the Paper Reviewing staff
        (a PRM, or a Referee / Editor / Reviewer of the target contribution),
        OR  a Session Coordinator has the rights to perform the request
    """

    def _checkProtection(self):
        if not (RCSessionCoordinator.hasRights(self) or RCContributionPaperReviewingStaff.hasRights(self)): 
            RHContribModifBase._checkProtection(self);

        
class RHContributionModification(RHContribModifBaseSpecialSesCoordAndReviewingStaffRights):
    _uh = urlHandlers.UHContributionModification
    
    def _checkParams(self, params):
        RHContribModifBase._checkParams(self, params)
        params["days"] = params.get("day", "all")
        if params.get("day", None) is not None :
            del params["day"]
    
    def _process(self):
        params = self._getRequestParams()
        if self._target.getOwner().isClosed():
            p = contributions.WPContributionModificationClosed(self, self._target)
        else:
            p = contributions.WPContributionModification(self, self._target)
            wf = self.getWebFactory()
            if wf != None:
                p = wf.getContributionModification(self, self._target)
        return p.display(**params)

class RHWithdraw(RHContribModifBaseSpecialSesCoordRights):
    _uh=urlHandlers.UHContribModWithdraw

    def _checkParams(self, params):
        RHContribModifBase._checkParams(self, params)
        self._action=""
        self._comment=""
        if params.has_key("REACTIVATE"):
            self._action="REACTIVATE"
        elif params.has_key("OK"):
            self._action="WITHDRAW"
            self._comment=params.get("comment", "")
        elif params.has_key("CANCEL"):
            self._action="CANCEL"
    
    def _process(self):
        url=urlHandlers.UHContributionModification.getURL(self._target)
        if self._action=="REACTIVATE":
            self._target.withdraw(self._getUser(), self._comment)
            self._redirect(url)
            return
        elif self._action=="WITHDRAW":
            self._target.withdraw(self._getUser(), self._comment)
            self._redirect(url)
            return
        elif self._action=="CANCEL":
            self._redirect(url)
            return
        p=contributions.WPModWithdraw(self, self._target)
        return p.display()


class RHContributionAC(RHContribModifBaseSpecialSesCoordAndReviewingStaffRights):
    _uh = urlHandlers.UHContribModifAC

    def _checkParams(self, params):
        RHContribModifBase._checkParams(self, params)
        params["days"] = params.get("day", "all")
        if params.get("day", None) is not None :
            del params["day"]
                
    def _process(self):
        params = self._getRequestParams()
        if self._target.getOwner().isClosed():
            p = contributions.WPContributionModificationClosed(self, self._target)
        else:
            p = contributions.WPContribModifAC(self, self._target)
            wf = self.getWebFactory()
            if wf != None:
                p = wf.getContribModifAC(self, self._target)
        return p.display(**params)


class RHContributionSC(RHContribModifBaseSpecialSesCoordAndReviewingStaffRights):
    _uh = urlHandlers.UHContribModifSubCont
    
    def _checkParams(self, params):
        RHContribModifBase._checkParams(self, params)
        params["days"] = params.get("day", "all")
        if params.get("day", None) is not None :
            del params["day"]
    
    def _process(self):
        params = self._getRequestParams()
        p = contributions.WPContribModifSC(self, self._target)
        wf = self.getWebFactory()
        if wf != None:
            p = wf.getContribModifSC(self, self._target)
        return p.display(**params)

class RHSubContribActions(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHSubContribActions

    def _checkParams(self, params):
        RHContribModifBase._checkParams(self, params)
        self._confirm = params.has_key("confirm")
        self._scIds = self._normaliseListParam(params.get("selSubContribs", []))
        self._action=None
        if "cancel" in params:
            return
        self._action=[]
        for id in self._scIds:
            sc = self._target.getSubContributionById(id)
            self._action.append(_ActionSubContribDelete(self, self._target, sc))
        if params.has_key("oldpos") and params["oldpos"]!='':
            self._action = _ActionSubContribMove(self, params['newpos'+params['oldpos']], params['oldpos'])

    def _process(self):
        if self._action is not None:
            if isinstance(self._action, list):
                for act in self._action:
                    act.perform()
            else:
                self._action.perform()
        self._redirect(urlHandlers.UHContribModifSubCont.getURL(self._target))

class _ActionSubContribDelete:

    def __init__(self, rh, target, sc):
        self._rh = rh
        self._target = target
        self._sc = sc

    def perform(self):
        self._target.removeSubContribution(self._sc)

class _ActionSubContribMove:

    def __init__(self, rh, newpos, oldpos):
        self._rh = rh
        self._newpos = int(newpos)
        self._oldpos = int(oldpos)

    def perform(self):
        scList = self._rh._target.getSubContributionList()
        order = 0
        movedsubcontrib = scList[self._oldpos]
        del scList[self._oldpos]
        scList.insert(self._newpos, movedsubcontrib)
        self._rh._target.notifyModification()

        #for sc in scList:
        #    sc.setOrder(scList.index(sc))
    
#-------------------------------------------------------------------------------------

class RHContributionAddSC(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContribAddSubCont
    
    def _process(self):
        p = contributions.WPContribAddSC(self, self._target)        
        params = self._getRequestParams()
        if params.get("recalled", None) is None :
            self._removePreservedParams()
            self._removeDefinedList("presenter")
        params.update(self._getPreservedParams())
        wf = self.getWebFactory()
        if wf != None:
            p = wf.getContribAddSC(self, self._target)
            
        params["presenterDefined"] = self._getDefinedDisplayList("presenter")
        params["presenterOptions"] = self._getPersonOptions("presenter")
        
        params["days"] = params.get("day", "all")
        if params.get("day", None) is not None :
            del params["day"]
        
        return p.display(**params)

    def _getDefinedDisplayList(self, typeName):
        return self._websession.getVar("%sList"%typeName)
    
    def _getPreservedParams(self):
        params = self._websession.getVar("preservedParams")
        if params is None :
            return {}
        return params
        
    def _removePreservedParams(self):
        self._websession.setVar("preservedParams", None)
    
    def _removeDefinedList(self, typeName):
        self._websession.setVar("%sList"%typeName, None)        
    
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
        for contribution in self._target.getConference().getContributionList() :
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

class RHContributionCreateSC(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContribCreateSubCont
    
    def _process(self):
        
        params = self._getRequestParams()
        #params.update(self._getPreservedParams())
        sc = self._target
        """self._target - contribution owning new subcontribution"""
        
        if ("ok" in params):            
            sc = self._target.newSubContribution()
            sc.setTitle( params.get("title", "") )
            sc.setDescription( params.get("description", "") )
            sc.setKeywords( params.get("keywords", "") )
            sc.setDuration( params.get("durationHours", ""), \
                             params.get("durationMinutes", "") )   
            sc.setSpeakerText( params.get("speakers", "") )
            sc.setParent(self._target)
            for presenter in self._getDefinedList("presenter") :
                sc.newSpeaker(presenter[0])
            
            logInfo = sc.getLogInfo()
            logInfo["subject"] = "Create new subcontribution: %s"%sc.getTitle()
            self._target.getConference().getLogHandler().logAction(logInfo, "Timetable/SubContribution", self._getUser())
                
            self._removePreservedParams()
            self._removeDefinedList("presenter")
            self._redirect(urlHandlers.UHContribModifSubCont.getURL(sc))
        elif params.get("performedAction", "") == "New presenter" :
            self._preserveParams(params)
            self._redirect(urlHandlers.UHContribCreateSubContPresenterNew.getURL(self._target))
        elif params.get("performedAction","") == "Search presenter" :
            self._preserveParams(params)
            self._redirect(urlHandlers.UHContribCreateSubContPresenterSearch.getURL(self._target))
        elif params.get("performedAction", "") == "Add as presenter" :
            self._preserveParams(params)
            url = urlHandlers.UHContribCreateSubContPersonAdd.getURL(self._target)
            url.addParam("typeName", "presenter")
            url.addParam("orgin", "added")
            self._redirect(url)
        elif params.get("performedAction", "") == "Remove presenters" :
            self._preserveParams(params)
            self._removePersons(params, "presenter")
            url = urlHandlers.UHContribAddSubCont.getURL(self._target)
            url.addParam("recalled", "true")
            self._redirect(url)
        else:        
            self._removePreservedParams()
            self._removeDefinedList("presenter")
            self._redirect(urlHandlers.UHContribModifSubCont.getURL(sc))    

    def _getPreservedParams(self):
        params = self._websession.getVar("preservedParams")
        if params is None :
            return {}
        return params
    
    def _preserveParams(self, params):
        self._websession.setVar("preservedParams", params)
        
    def _removePreservedParams(self):
        self._websession.setVar("preservedParams", None)
        
    def _getDefinedList(self, typeName):
        definedList = self._websession.getVar("%sList"%typeName)
        if definedList is None :
            return []
        return definedList
    
    def _setDefinedList(self, definedList, typeName):
        self._websession.setVar("%sList"%typeName, definedList)
    
    def _removeDefinedList(self, typeName):
        self._websession.setVar("%sList"%typeName, None)        

    def _removePersons(self, params, typeName):
        persons = self._normaliseListParam(params.get("%ss"%typeName, []))
        definedList = self._getDefinedList(typeName)
        personsToRemove = []
        for p in persons :
            if int(p) < len(definedList) or int(p) >= 0 :
                personsToRemove.append(definedList[int(p)])
        for person in personsToRemove :
            definedList.remove(person)
        self._setDefinedList(definedList, typeName)        

#-------------------------------------------------------------------------------------

class RHNewSubcontributionPresenterSearch(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContribCreateSubContPresenterSearch

    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        
    def _process(self):
        params = self._getRequestParams()
        
        params["newButtonAction"] = str(urlHandlers.UHContribCreateSubContPresenterNew.getURL())
        addURL = urlHandlers.UHContribCreateSubContPersonAdd.getURL()
        addURL.addParam("orgin", "selected")
        addURL.addParam("typeName", "presenter")
        params["addURL"] = addURL
        p = contributions.WSubContributionCreationPresenterSelect(self, self._target)
        return p.display(**params)

#-------------------------------------------------------------------------------------

class RHNewSubcontributionPresenterNew(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContribCreateSubContPresenterNew

    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        
    def _process(self):
        p = contributions.WSubContributionCreationPresenterNew(self, self._target)
        return p.display()

#-------------------------------------------------------------------------------------

class RHNewSubcontributionPersonAdd(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContribCreateSubContPersonAdd

    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        self._typeName = params.get("typeName", None)
        if self._typeName  is None :
            raise MaKaCError( _("Type name of the person to add is not set."))        
        
    def _process(self):
        params = self._getRequestParams()
        self._errorList = []        
        
        definedList = self._getDefinedList(self._typeName)
        if definedList is None :
            definedList = []
        
        if params.get("orgin", "") == "new" :
            if params.get("ok", None) is None :
                url = urlHandlers.UHContribAddSubCont.getURL(self._target)
                url.addParam("recalled", "true")
                self._redirect(url)
                return
            else :
                person = SubContribParticipation()
                person.setFirstName(params["name"])
                person.setFamilyName(params["surName"])
                person.setEmail(params["email"])
                person.setAffiliation(params["affiliation"])
                person.setAddress(params["address"])
                person.setPhone(params["phone"])
                person.setTitle(params["title"])
                person.setFax(params["fax"])                
                if not self._alreadyDefined(person, definedList) :
                    definedList.append([person, params.has_key("submissionControl")])
                else :
                    self._errorList.append("%s has been already defined as %s of this session"%(person.getFullName(), self._typeName))
        
        elif params.get("orgin", "") == "selected" :
            selectedList = self._normaliseListParam(self._getRequestParams().get("selectedPrincipals", []))
            
            for s in selectedList :
                if s[0:8] == "*author*" :
                    auths = self._target.getConference().getAuthorIndex()
                    selected = auths.getById(s[9:])[0]
                else :
                    ph = user.PrincipalHolder()
                    selected = ph.getById(s)                            
                if isinstance(selected, user.Avatar) :                    
                    person = SubContribParticipation()
                    person.setDataFromAvatar(selected)
                    if not self._alreadyDefined(person, definedList) :                        
                        definedList.append([person, params.has_key("submissionControl")])
                    else :                        
                        self._errorList.append("%s has been already defined as %s of this session"%(person.getFullName(), self._typeName))
                        
                elif isinstance(selected, user.Group) : 
                    for member in selected.getMemberList() :
                        person = SubContribParticipation()
                        person.setDataFromAvatar(member)
                        if not self._alreadyDefined(person, definedList) :
                            definedList.append([person, params.has_key("submissionControl")])            
                        else :
                            self._errorList.append("%s has been already defined as %s of this session"%(person.getFullName(), self._typeName))
                else : 
                    person = SubContribParticipation()                                            
                    person.setTitle(selected.getTitle())
                    person.setFirstName(selected.getFirstName())
                    person.setFamilyName(selected.getFamilyName())
                    person.setEmail(selected.getEmail())
                    person.setAddress(selected.getAddress())
                    person.setAffiliation(selected.getAffiliation())
                    person.setPhone(selected.getPhone())
                    person.setFax(selected.getFax())
                    if not self._alreadyDefined(person, definedList) :
                        definedList.append([person, params.has_key("submissionControl")])
                    else :
                        self._errorList.append("%s has been already defined as %s of this session"%(person.getFullName(), self._typeName))
                
        elif params.get("orgin", "") == "added" :        
            preservedParams = self._getPreservedParams()
            chosen = preservedParams.get("%sChosen"%self._typeName, None)
            if chosen is None or chosen == "" : 
                url = urlHandlers.UHContribAddSubCont.getURL(self._target)
                url.addParam("recalled", "true")
                self._redirect(url)
                return            
            index = chosen.find("-")
            objectId = chosen[1:index]
            chosenId = chosen[index+1:len(chosen)]
            if chosen[0:1] == "d" :                
                object = self._target.getConference().getSessionById(objectId)
            else :
                object = self._target.getConference().getContributionById(objectId)
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
            person = SubContribParticipation()                                            
            person.setTitle(chosenPerson.getTitle())
            person.setFirstName(chosenPerson.getFirstName())
            person.setFamilyName(chosenPerson.getFamilyName())
            person.setEmail(chosenPerson.getEmail())
            person.setAddress(chosenPerson.getAddress())
            person.setAffiliation(chosenPerson.getAffiliation())
            person.setPhone(chosenPerson.getPhone())
            person.setFax(chosenPerson.getFax())
            if not self._alreadyDefined(person, definedList) :
                definedList.append([person, params.has_key("submissionControl")])    
            else :
                self._errorList.append("%s has been already defined as %s of this session"%(person.getFullName(), self._typeName))
        else :
            self._redirect(urlHandlers.UHConfModifSchedule.getURL(self._target))
            return
        preservedParams = self._getPreservedParams()
        preservedParams["errorMsg"] = self._errorList
        self._preserveParams(preservedParams)
        self._websession.setVar("%sList"%self._typeName, definedList)
        
        url = urlHandlers.UHContribAddSubCont.getURL(self._target)
        url.addParam("recalled", "true")
        self._redirect(url)


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
        self._websession.setVar("preservedParams", params)
        
    def _removePreservedParams(self):
        self._websession.setVar("preservedParams", None)

#-------------------------------------------------------------------------------------


#class RHContributionDeleteSC( RHContribModifBase ):
#    _uh = urlHandlers.UHContriDeleteSubCont
#    
#    def _checkParams( self, params ):
#        RHContribModifBase._checkParams( self, params )
#        self._confirm = params.has_key( "confirm" )
#        self._cancel = params.has_key( "cancel" ) 
#        self._scIds = self._normaliseListParam( params.get("selSubContribs", []) )

#    def _process( self ):
#        for id in self._scIds:
#            sc = self._target.getSubContributionById( id )
#            self._target.removeSubContribution( sc )
#        self._redirect( urlHandlers.UHContribModifSubCont.getURL( self._target ) )


class RHContributionUpSC(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContribUpSubCont
    
    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        self._scId = params.get("subContId", "") 

    def _process(self):
        sc = self._target.getSubContributionById(self._scId)
        self._target.upSubContribution(sc)
        self._redirect(urlHandlers.UHContribModifSubCont.getURL(self._target))
        

class RHContributionDownSC(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContribDownSubCont
    
    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        self._scId = params.get("subContId", "") 

    def _process(self):
        sc = self._target.getSubContributionById(self._scId)
        self._target.downSubContribution(sc)
        self._redirect(urlHandlers.UHContribModifSubCont.getURL(self._target))
        

class RHContributionTools(RHContribModifBaseSpecialSesCoordAndReviewingStaffRights):
    _uh = urlHandlers.UHContribModifTools
    
    def _process(self):
        if self._target.getOwner().isClosed():
            p = contributions.WPContributionModificationClosed(self, self._target)
        else:
            p = contributions.WPContributionModifTools(self, self._target)
            wf = self.getWebFactory()
            if wf != None:
                p = wf.getContributionModifTools(self, self._target)
        return p.display()


class RHContributionData( RoomBookingDBMixin, RHContribModifBaseSpecialSesCoordRights ):
    _uh = urlHandlers.UHContributionDataModif

    def _checkParams( self, params ):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        
        self._evt = self._target
    
    def _process(self):
        if self._target.getOwner().isClosed():
            p = contributions.WPContributionModificationClosed(self, self._target)
        else:
            p = contributions.WPEditData(self, self._target)
            wf = self.getWebFactory()
            if wf != None:
                p = wf.getContributionEditData(self, self._target)
        return p.display(**self._getRequestParams())


class RHContributionModifData(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContributionDataModification

    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        self._type=None
        self._check = int(params.get("check", 1))
        if params.has_key("type") and params["type"].strip()!="":
            self._type=self._target.getConference().getContribTypeById(params["type"])
        self._cancel = params.has_key("cancel")
    
    def _process(self):
        if not self._cancel:
            params = self._getRequestParams()

            if params.has_key("dateTime"):
                dateTime = parseDateTime(params["dateTime"])
                params["sYear"] = dateTime.year
                params["sMonth"] = dateTime.month
                params["sDay"] = dateTime.day
                params["sHour"] = dateTime.hour
                params["sMinute"] = dateTime.minute
            else:
                params["sYear"] = ""
                params["sMonth"] = ""
                params["sDay"] = ""
                params["sHour"] = ""
                params["sMinute"] = ""

            if params.has_key("duration"):
                params["durMins"] = params["duration"];
            else:
                params["durMins"] = ""
            self._target.setValues(params)
            self._target.setType(self._type)
        self._redirect(urlHandlers.UHContributionModification.getURL(self._target))


class RHSearchPrimaryAuthor (RHContribModifBaseSpecialSesCoordRights):
    def _process(self):
        p=contributions.WPModSearchPrimAuthor(self, self._target)
        return p.display(**self._getRequestParams())

class RHSearchAddPrimaryAuthor (RHContribModifBaseSpecialSesCoordRights):

    def _newPrimAuthor(self, a):
        auth = conference.ContributionParticipation()
        p = self._getRequestParams()
        auth.setTitle(a.getTitle())
        auth.setFirstName(a.getName())
        auth.setFamilyName(a.getSurName())
        auth.setAffiliation(a.getOrganisation())
        auth.setEmail(a.getEmail())
        auth.setAddress(a.getAddress())
        auth.setPhone(a.getTelephone())
        auth.setFax(a.getFax())
        self._target.addPrimaryAuthor(auth)
        return auth

    def _newPrimAuthorFromAuthor(self, a):
        auth = conference.ContributionParticipation()
        p = self._getRequestParams()
        auth.setTitle(a.getTitle())
        auth.setFirstName(a.getName())
        auth.setFamilyName(a.getSurName())
        auth.setAffiliation(a.getAffiliation())
        auth.setEmail(a.getEmail())
        auth.setAddress(a.getAddress())
        auth.setPhone(a.getPhone())
        auth.setFax(a.getFax())
        self._target.addPrimaryAuthor(auth)
        return auth
        
    def _process(self):
        params=self._getRequestParams()
        if "selectedPrincipals" in params:
            ah=user.AvatarHolder()
            authIndex = self._target.getConference().getAuthorIndex()
            for id in self._normaliseListParam(params["selectedPrincipals"]):
                if id[:9] == "*author*:":
                    id = id[9:]
                    auth=self._newPrimAuthorFromAuthor(authIndex.getById(id)[0])
                else:
                    auth=self._newPrimAuthor(ah.getById(id))
                if self._getRequestParams().has_key("submissionControl"):
                    self._target.grantSubmission(auth)
        self._redirect(urlHandlers.UHContributionModification.getURL(self._target))

class RHSearchCoAuthor (RHContribModifBaseSpecialSesCoordRights):
    def _process(self):
        p=contributions.WPModSearchCoAuthor(self, self._target)
        return p.display(**self._getRequestParams())

class RHSearchAddCoAuthor (RHContribModifBaseSpecialSesCoordRights):

    def _newCoAuthor(self, a):
        auth = conference.ContributionParticipation()
        p = self._getRequestParams()
        auth.setTitle(a.getTitle())
        auth.setFirstName(a.getName())
        auth.setFamilyName(a.getSurName())
        auth.setAffiliation(a.getOrganisation())
        auth.setEmail(a.getEmail())
        auth.setAddress(a.getAddress())
        auth.setPhone(a.getTelephone())
        auth.setFax(a.getFax())
        self._target.addCoAuthor(auth)
        return auth

    def _newCoAuthorFromAuthor(self, a):
        auth = conference.ContributionParticipation()
        p = self._getRequestParams()
        auth.setTitle(a.getTitle())
        auth.setFirstName(a.getName())
        auth.setFamilyName(a.getSurName())
        auth.setAffiliation(a.getAffiliation())
        auth.setEmail(a.getEmail())
        auth.setAddress(a.getAddress())
        auth.setPhone(a.getPhone())
        auth.setFax(a.getFax())
        self._target.addCoAuthor(auth)
        return auth
        
    def _process(self):
        params=self._getRequestParams()
        if "selectedPrincipals" in params:
            ah=user.AvatarHolder()
            authIndex = self._target.getConference().getAuthorIndex()
            for id in self._normaliseListParam(params["selectedPrincipals"]):
                if id[:9] == "*author*:":
                    id = id[9:]
                    auth=self._newCoAuthorFromAuthor(authIndex.getById(id)[0])
                else:
                    auth=self._newCoAuthor(ah.getById(id))
                if self._getRequestParams().has_key("submissionControl"):
                    self._target.grantSubmission(auth)
        self._redirect(urlHandlers.UHContributionModification.getURL(self._target))


class RHSearchSpeakers (RHContribModifBaseSpecialSesCoordRights):
    def _process(self):
        p=contributions.WPModSearchSpeaker(self, self._target)
        return p.display(**self._getRequestParams())

class RHSearchAddSpeakers (RHContribModifBaseSpecialSesCoordRights):

    def _newSpeaker(self, a):
        auth = conference.ContributionParticipation()
        p = self._getRequestParams()
        auth.setTitle(a.getTitle())
        auth.setFirstName(a.getName())
        auth.setFamilyName(a.getSurName())
        auth.setAffiliation(a.getOrganisation())
        auth.setEmail(a.getEmail())
        auth.setAddress(a.getAddress())
        auth.setPhone(a.getTelephone())
        auth.setFax(a.getFax())
        self._target.newSpeaker(auth)
        return auth

    def _newSpeakerFromAuthor(self, a):
        auth = conference.ContributionParticipation()
        p = self._getRequestParams()
        auth.setTitle(a.getTitle())
        auth.setFirstName(a.getName())
        auth.setFamilyName(a.getSurName())
        auth.setAffiliation(a.getAffiliation())
        auth.setEmail(a.getEmail())
        auth.setAddress(a.getAddress())
        auth.setPhone(a.getPhone())
        auth.setFax(a.getFax())
        self._target.newSpeaker(auth)
        return auth
        
    def _process(self):
        params=self._getRequestParams()
        if "selectedPrincipals" in params:
            ah=user.AvatarHolder()
            authIndex = self._target.getConference().getAuthorIndex()
            for id in self._normaliseListParam(params["selectedPrincipals"]):
                if id[:9] == "*author*:":
                    id = id[9:]
                    auth=self._newSpeakerFromAuthor(authIndex.getById(id)[0])
                else:
                    auth=self._newSpeaker(ah.getById(id))
                if self._getRequestParams().has_key("submissionControl"):
                    self._target.grantSubmission(auth)
        self._redirect(urlHandlers.UHContributionModification.getURL(self._target))

class RHNewPrimaryAuthor(RHContribModifBaseSpecialSesCoordRights):
    
    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        self._action, self._new="", False
        if params.has_key("ok"):
            self._action = "perform"
        elif params.has_key("ok_and_new"):
            self._action = "perform"
            self._new=True
        elif params.has_key("cancel"):
            self._action = "cancel"

    def _newPrimAuthor(self):
        auth = conference.ContributionParticipation()
        p = self._getRequestParams()
        auth.setTitle(p.get("title", ""))
        auth.setFirstName(p.get("name", ""))
        auth.setFamilyName(p.get("surName", ""))
        auth.setAffiliation(p.get("affiliation", ""))
        auth.setEmail(p.get("email", ""))
        auth.setAddress(p.get("address", ""))
        auth.setPhone(p.get("phone", ""))
        auth.setFax(p.get("fax", ""))
        self._target.addPrimaryAuthor(auth)
        return auth
            
    
    def _process(self):
        url=urlHandlers.UHContributionModification.getURL(self._target)
        if self._action=="cancel":
            self._redirect(url)
            return
        elif self._action == "perform":
            auth=self._newPrimAuthor()
            if self._getRequestParams().has_key("submissionControl"):
                if self._getRequestParams().get("email", "").strip() == "":
                    raise FormValuesError("If you want to add the author as submitter, please enter their email")
                self._target.grantSubmission(auth)
            if not self._new:
                self._redirect(url)
                return
        p = contributions.WPModNewPrimAuthor(self, self._target)
        return p.display()


class RHPrimaryAuthorsActions:
    """
    class to select the action to do with the selected authors
    """
    def __init__(self, req):
        self._req = req
    
    def process(self, params):
        if params.has_key("REMOVE"):
            return RHRemPrimaryAuthors(self._req).process(params)
        elif params.has_key("MOVE"):
            return RHMovePrimaryToCoAuthors(self._req).process(params)
        return "no action to do"


class RHRemPrimaryAuthors(RHContribModifBaseSpecialSesCoordRights):
    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        self._list = []
        for id in self._normaliseListParam(params.get("selAuthor", [])):
            self._list.append(self._target.getAuthorById(id))

    def _process(self):
        for auth in self._list:
            self._target.removePrimaryAuthor(auth)
        url=urlHandlers.UHContributionModification.getURL(self._target)
        self._redirect(url)

class RHMovePrimaryToCoAuthors(RHContribModifBaseSpecialSesCoordRights):
    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        self._list = []
        for id in self._normaliseListParam(params.get("selAuthor", [])):
            self._list.append(self._target.getAuthorById(id))

    def _process(self):
        for auth in self._list:
            self._target.removePrimaryAuthor(auth, 0, False)
            self._target.addCoAuthor(auth)
        url=urlHandlers.UHContributionModification.getURL(self._target)
        self._redirect(url)
        

class RHEditPrimaryAuthor(RHContribModifBaseSpecialSesCoordRights):
    
    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        self._authorId=params["authorId"]
        self._action=""
        if params.has_key("ok"):
            self._action = "perform"
        elif params.has_key("cancel"):
            self._action = "cancel"

    def _setPrimAuthorData(self):
        auth=self._target.getAuthorById(self._authorId)
        p = self._getRequestParams()
        auth.setTitle(p.get("title", ""))
        auth.setFirstName(p.get("name", ""))
        auth.setFamilyName(p.get("surName", ""))
        auth.setAffiliation(p.get("affiliation", ""))
        auth.setAddress(p.get("address", ""))
        auth.setPhone(p.get("phone", ""))
        auth.setFax(p.get("fax", ""))

        grantSubm=False
        if auth.getEmail().lower().strip() != p.get("email", "").lower().strip():
            #----If it's already in the pending queue in order to grant 
            #    submission rights we must unindex and after the modification of the email,
            #    index again...
            if self._target.getConference().getPendingQueuesMgr().isPendingSubmitter(auth):
                self._target.getConference().getPendingQueuesMgr().removePendingSubmitter(auth)
                grantSubm=True
            #-----
            
        auth.setEmail(p.get("email", ""))
        
        if grantSubm:
            self._target.grantSubmission(auth)
    
    def _process(self):
        if self._action != "":
            if self._action == "perform":
                self._setPrimAuthorData()
            url=urlHandlers.UHContributionModification.getURL(self._target)
            self._redirect(url)
        else:
            auth=self._target.getAuthorById(self._authorId)
            p = contributions.WPModPrimAuthor(self, self._target)
            return p.display(author=auth)


class RHNewCoAuthor(RHContribModifBaseSpecialSesCoordRights):
    
    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        self._action, self._new="", False
        if params.has_key("ok"):
            self._action = "perform"
        elif params.has_key("ok_and_new"):
            self._action = "perform"
            self._new=True
        elif params.has_key("cancel"):
            self._action = "cancel"

    def _newCoAuthor(self):
        auth = conference.ContributionParticipation()
        p = self._getRequestParams()
        auth.setTitle(p.get("title", ""))
        auth.setFirstName(p.get("name", ""))
        auth.setFamilyName(p.get("surName", ""))
        auth.setAffiliation(p.get("affiliation", ""))
        auth.setEmail(p.get("email", ""))
        auth.setAddress(p.get("address", ""))
        auth.setPhone(p.get("phone", ""))
        auth.setFax(p.get("fax", ""))
        self._target.addCoAuthor(auth)
        return auth
    
    def _process(self):
        url=urlHandlers.UHContributionModification.getURL(self._target)
        if self._action=="cancel":
            self._redirect(url)
            return
        elif self._action=="perform":
            auth=self._newCoAuthor()
            if self._getRequestParams().has_key("submissionControl"):
                if self._getRequestParams().get("email", "").strip() == "":
                    raise FormValuesError("If you want to add the author as submitter, please enter their email")
                self._target.grantSubmission(auth)
            if not self._new:
                self._redirect(url)
                return
        p=contributions.WPModNewCoAuthor(self, self._target)
        return p.display()


class RHCoAuthorsActions:
    """
    class to select the action to do with the selected authors
    """
    def __init__(self, req):
        self._req = req
    
    def process(self, params):
        if params.has_key("REMOVE"):
            return RHRemCoAuthors(self._req).process(params)
        elif params.has_key("MOVE"):
            return RHMoveCoToPrimaryAuthors(self._req).process(params)
        return "no action to do"


class RHRemCoAuthors(RHContribModifBaseSpecialSesCoordRights):
    
    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        self._list = []
        for id in self._normaliseListParam(params.get("selAuthor", [])):
            self._list.append(self._target.getAuthorById(id))

    def _process(self):
        for auth in self._list:
            self._target.removeCoAuthor(auth)
        url=urlHandlers.UHContributionModification.getURL(self._target)
        self._redirect(url)

class RHMoveCoToPrimaryAuthors(RHContribModifBaseSpecialSesCoordRights):
    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        self._list = []
        for id in self._normaliseListParam(params.get("selAuthor", [])):
            self._list.append(self._target.getAuthorById(id))

    def _process(self):
        for auth in self._list:
            self._target.removeCoAuthor(auth, 0, False)
            self._target.addPrimaryAuthor(auth)
        url=urlHandlers.UHContributionModification.getURL(self._target)
        self._redirect(url)

class RHEditCoAuthor(RHContribModifBaseSpecialSesCoordRights):
    
    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        self._authorId=params["authorId"]
        self._action=""
        if params.has_key("ok"):
            self._action = "perform"
        elif params.has_key("cancel"):
            self._action = "cancel"

    def _setCoAuthorData(self):
        auth=self._target.getAuthorById(self._authorId)
        p = self._getRequestParams()
        auth.setTitle(p.get("title", ""))
        auth.setFirstName(p.get("name", ""))
        auth.setFamilyName(p.get("surName", ""))
        auth.setAffiliation(p.get("affiliation", ""))
        auth.setAddress(p.get("address", ""))
        auth.setPhone(p.get("phone", ""))
        auth.setFax(p.get("fax", ""))

        grantSubm=False
        if auth.getEmail().lower().strip() != p.get("email", "").lower().strip():
            #----If it's already in the pending queue in order to grant 
            #    submission rights we must unindex and after the modification of the email,
            #    index again...
            if self._target.getConference().getPendingQueuesMgr().isPendingSubmitter(auth):
                self._target.getConference().getPendingQueuesMgr().removePendingSubmitter(auth)
                grantSubm=True
            #-----
        
        auth.setEmail(p.get("email", ""))
        
        if grantSubm:
            self._target.grantSubmission(auth)
    
    def _process(self):
        if self._action != "":
            if self._action == "perform":
                self._setCoAuthorData()
            url=urlHandlers.UHContributionModification.getURL(self._target)
            self._redirect(url)
        else:
            auth=self._target.getAuthorById(self._authorId)
            p = contributions.WPModCoAuthor(self, self._target)
            return p.display(author=auth)


class RHRemSpeakers(RHContribModifBaseSpecialSesCoordRights):
    
    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        self._list = []
        for id in self._normaliseListParam(params.get("selSpeaker", [])):
            self._list.append(self._target.getSpeakerById(id))

    def _process(self):
        for auth in self._list:
            if auth is None:
                continue
            self._target.removeSpeaker(auth)
        url=urlHandlers.UHContributionModification.getURL(self._target)
        self._redirect(url)
        

class RHAddSpeakers(RHContribModifBaseSpecialSesCoordRights):
    
    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        self._list = []
        for id in self._normaliseListParam(params.get("selAuthor", [])):
            self._list.append(self._target.getAuthorById(id))

    def _process(self):
        for auth in self._list:
            if auth is None:
                continue
            self._target.addSpeaker(auth)
        url=urlHandlers.UHContributionModification.getURL(self._target)
        self._redirect(url)


class RHSetTrack(RHContribModifBase):
        
    def _checkParams(self, params):
        RHContribModifBase._checkParams(self, params)
        self._track=None
        if params.has_key("selTrack") and params["selTrack"].strip() != "":
            self._track = self._target.getConference().getTrackById(params["selTrack"])
    
    def _process(self):
        self._target.setTrack(self._track)
        url=urlHandlers.UHContributionModification.getURL(self._target)
        self._redirect(url)


class RHSetSession(RHContribModifBase):
        
    def _checkParams(self, params):
        RHContribModifBase._checkParams(self, params)
        self._session=None
        if params.has_key("selSession") and params["selSession"].strip() != "":
            self._session=self._target.getConference().getSessionById(params["selSession"])
    
    def _process(self):
        self._target.setSession(self._session)
        url=urlHandlers.UHContributionModification.getURL(self._target)
        self._redirect(url)


#class RHContributionSelectSpeakers( RHContribModifBase ):
#    _uh = urlHandlers.UHContributionSelectSpeakers
#    
#    def _process( self ):
#        p = contributions.WPcontribSelectChairs( self, self._target )
#        return p.display( **self._getRequestParams() )
#
#
#class RHContributionAddSpeakers( RHContribModifBase ):
#    _uh = urlHandlers.UHContributionAddSpeakers
#    
#    def _checkParams( self, params ):
#        RHContribModifBase._checkParams( self, params )
#        selSpeakerId = self._normaliseListParam( params.get( "selectedPrincipals", [] ) )
#        ah = user.AvatarHolder()
#        self._speakers = []
#        for id in selSpeakerId:
#            self._speakers.append( ah.getById( id ) )
#    
#    def _process( self ):
#        for av in self._speakers:
#            self._target.addSpeaker( av )
#        self._redirect( urlHandlers.UHContributionModification.getURL( self._target ) )
#
#
#class RHContributionRemoveSpeakers( RHContribModifBase ):
#    _uh = urlHandlers.UHContributionRemoveSpeakers
#    
#    def _checkParams( self, params ):
#        RHContribModifBase._checkParams( self, params )
#        selSpeakerId = self._normaliseListParam( params.get( "selectedPrincipals", [] ) )
#        ah = user.AvatarHolder()
#        self._speakers = []
#        for id in selSpeakerId:
#            self._speakers.append( ah.getById( id ) )
#    
#    def _process( self ):
#        for av in self._speakers:
#            self._target.removeSpeaker( av )
#        self._redirect( urlHandlers.UHContributionModification.getURL( self._target ) )


class RHContributionAddMaterial(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContributionAddMaterial
    
    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        typeMat = params.get("typeMaterial", "notype")
        if typeMat=="notype" or typeMat.strip()=="":
            raise FormValuesError("Please choose a material type")
        self._mf = materialFactories.ContribMFRegistry().getById(typeMat)
        
    def _process(self):
        if self._mf:
            if not self._mf.needsCreationPage():
                m = RHContributionPerformAddMaterial.create(self._target, self._mf, self._getRequestParams())
                self._redirect(urlHandlers.UHMaterialModification.getURL(m))
                return 
        p = contributions.WPContribAddMaterial(self, self._target, self._mf)
        wf = self.getWebFactory()
        if wf != None:
            p = wf.getContribAddMaterial(self, self._target, self._mf)
        return p.display()


class RHContributionPerformAddMaterial(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContributionPerformAddMaterial
    
    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        typeMat = params.get("typeMaterial", "")
        self._mf = materialFactories.ContribMFRegistry.getById(typeMat)

    @staticmethod
    def create(contrib, matFactory, matData):
        if matFactory:
            m = matFactory.create(contrib)
        else:
            m = conference.Material()
            contrib.addMaterial(m)
            m.setValues(matData)
        return m

    def _process(self):
        m = self.create(self._target, self._mf, self._getRequestParams())
        self._redirect(urlHandlers.UHMaterialModification.getURL(m))


class RHContributionRemoveMaterials(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContributionRemoveMaterials
    
    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        #typeMat = params.get( "typeMaterial", "" )
        #self._mf = materialFactories.ConfMFRegistry().getById( typeMat )
        self._materialIds = self._normaliseListParam(params.get("deleteMaterial", []))
        self._materialIds = self._normaliseListParam( params.get("materialId", []) )
        self._returnURL = params.get("returnURL","")
    
    def _process(self):
        for id in self._materialIds:
            #Performing the deletion of special material types
            f = materialFactories.ContribMFRegistry().getById(id)
            if f:
                f.remove(self._target)
            else:
                #Performs the deletion of additional material types
                mat = self._target.getMaterialById( id )
                self._target.removeMaterial( mat )
        if self._returnURL != "":
            url = self._returnURL
        else:
            url = urlHandlers.UHContribModifMaterials.getURL( self._target )
        self._redirect( url )


class RHMaterialsAdd(RHContribModifBase):
    _uh = urlHandlers.UHContribModifAddMaterials

    def _checkProtection(self):
        material = self._rhSubmitMaterial._getMaterial()
        if self._target.canUserSubmit(self._aw.getUser()) \
            and material.getReviewingState() < 3:
            return
        RHContribModifBase._checkProtection(self)

    def _checkParams(self, params):
        RHContribModifBase._checkParams(self, params)
        if not hasattr(self,"_rhSubmitMaterial"):
            self._rhSubmitMaterial=RHSubmitMaterialBase(self._target, self)
        self._rhSubmitMaterial._checkParams(params)    
    
    def _process( self ):
        if self._target.getConference().isClosed():
            p = WPConferenceModificationClosed( self, self._target )
            return p.display()
        else:
            r=self._rhSubmitMaterial._process(self, self._getRequestParams())
        if r is None:
            self._redirect(self._uh.getURL(self._target))
        
        return r

class RHContributionSelectManagers(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContributionSelectManagers
    
    def _process(self):
        p = contributions.WPContributionSelectManagers(self, self._target)
        return p.display(**self._getRequestParams())


class RHContributionAddManagers(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContributionAddManagers
    
    def _process(self):
        params = self._getRequestParams()
        if "selectedPrincipals" in params:
            ph = user.PrincipalHolder()
            for id in self._normaliseListParam(params["selectedPrincipals"]):
                self._target.grantModification(ph.getById(id))
        self._redirect(urlHandlers.UHContribModifAC.getURL(self._target))


class RHContributionRemoveManagers(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContributionRemoveManagers
    
    def _process(self):
        params = self._getRequestParams()
        if ("selectedPrincipals" in params) and \
            (len(params["selectedPrincipals"])!=0):
            ph = user.PrincipalHolder()
            for id in self._normaliseListParam(params["selectedPrincipals"]):
                self._target.revokeModification(ph.getById(id))
        self._redirect(urlHandlers.UHContribModifAC.getURL(self._target))


class RHContributionSetVisibility(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContributionSetVisibility
    
    def _process(self):
        params = self._getRequestParams()
        privacy = params.get("visibility","PUBLIC")
        self._protect = 0
        if privacy == "PRIVATE":
            self._protect = 1
        elif privacy == "PUBLIC":
            self._protect = 0
        elif privacy == "ABSOLUTELY PUBLIC":
            self._protect = -1
        self._target.setProtection(self._protect)
        self._redirect(urlHandlers.UHContribModifAC.getURL(self._target))
    

class RHContributionSelectAllowed(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContributionSelectAllowed
    
    def _process(self):
        p = contributions.WPContributionSelectAllowed(self, self._target)
        return p.display(**self._getRequestParams())


class RHContributionAddAllowed(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContributionAddAllowed
    
    def _process(self):
        params = self._getRequestParams()
        if "selectedPrincipals" in params:
            ph = user.PrincipalHolder()
            for id in self._normaliseListParam(params["selectedPrincipals"]):
                self._target.grantAccess(ph.getById(id))
        self._redirect(urlHandlers.UHContribModifAC.getURL(self._target))


class RHContributionRemoveAllowed(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContributionRemoveAllowed
    
    def _process(self):
        params = self._getRequestParams()
        if ("selectedPrincipals" in params) and \
            (len(params["selectedPrincipals"])!=0):
            ph = user.PrincipalHolder()
            for id in self._normaliseListParam(params["selectedPrincipals"]):
                self._target.revokeAccess(ph.getById(id))
        self._redirect(urlHandlers.UHContribModifAC.getURL(self._target))


class RHContributionAddDomains(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContributionAddDomain
    
    def _process(self):
        params = self._getRequestParams()
        if ("addDomain" in params) and (len(params["addDomain"])!=0):
            dh = domain.DomainHolder()
            for domId in self._normaliseListParam(params["addDomain"]):
                self._target.requireDomain(dh.getById(domId))
        self._redirect(urlHandlers.UHContribModifAC.getURL(self._target))


class RHContributionRemoveDomains(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContributionRemoveDomain
    
    def _process(self):
        params = self._getRequestParams()
        if ("selectedDomain" in params) and (len(params["selectedDomain"])!=0):
            dh = domain.DomainHolder()
            for domId in self._normaliseListParam(params["selectedDomain"]):
                self._target.freeDomain(dh.getById(domId))
        #self._endRequest()
        self._redirect(urlHandlers.UHContribModifAC.getURL(self._target))


class RHContributionDeletion(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContributionDelete
    
    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        self._cancel = False
        if "cancel" in params:
            self._cancel = True
        self._confirmation = params.has_key("confirm")
    
    def _perform(self):
        conf = self._target.getConference()
        self._target.getOwner().getSchedule().removeEntry(self._target.getSchEntry())
        #self._target.getOwner().removeContribution(self._target)
        self._target.delete()
        #conf.removeContribution(self._target)
    
    def _process(self):
        if self._cancel:
            self._redirect(urlHandlers.UHContribModifTools.getURL(self._target))
        elif self._confirmation:
            owner = self._target.getOwner()
            self._perform()
            if self._target.getSession():
                self._redirect(urlHandlers.UHsessionModification.getURL(owner))
            else:
                self._redirect(urlHandlers.UHConferenceModification.getURL(owner))
        else:
            p = contributions.WPContributionDeletion(self, self._target)
            return p.display()


class RHContributionMove(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContributionMove
    
    def _process(self):
        p = contributions.WPcontribMove(self, self._target)
        return p.display(**self._getRequestParams())


class RHContributionPerformMove(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContributionPerformMove
    
    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        self._dest = params["Destination"]
    
    def _process(self):
        conf = self._target.getConference()
        if self._dest == 'CONF':
            newOwner = conf
        else:
            newOwner = conf.getSessionById(self._dest)
        self._moveContrib(newOwner)
        self._redirect(urlHandlers.UHContribModifTools.getURL(self._target))
        
        return "done"
    
    def _moveContrib(self, newOwner):
        owner = self._target.getOwner()
        owner.removeContribution(self._target)
        newOwner.addContribution(self._target)


class RHContributionWriteMinutes(RHContribModifBaseSpecialSesCoordRights):
    _uh = urlHandlers.UHContributionWriteMinutes

    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        self._cancel = params.has_key("cancel")
        self._save = params.has_key("OK")
        self._text = params.get("text", "")#.strip()

    def _process(self):
        if self._cancel:
            self._redirect(urlHandlers.UHContribModifTools.getURL(self._target))
        elif self._save:
            #if self._text!="":
                minutes = self._target.getMinutes()
                if not minutes:
                    minutes = self._target.createMinutes()
                minutes.setText(self._text)
                self._redirect(urlHandlers.UHContribModifTools.getURL(self._target))
        else:
            p = contributions.WPContributionWriteMinutes(self, self._target)
            return p.display()

class RHContributionToXML(RHContributionModification):
    _uh = urlHandlers.UHContribToXMLConfManager
    
    def _process(self):
        filename = "%s - contribution.xml"%self._target.getTitle()
        x = XMLGen()
        x.openTag("contribution")
        x.writeTag("Id", self._target.getId())
        x.writeTag("Title", self._target.getTitle())
        x.writeTag("Description", self._target.getDescription())
        afm = self._target.getConference().getAbstractMgr().getAbstractFieldsMgr()
        for f in afm.getFields():
            id = f.getId()
            if f.isActive() and self._target.getField(id).strip() != "":
                x.writeTag(id.replace(" ","_"),self._target.getField(id))
        x.writeTag("Conference", self._target.getConference().getTitle())
        session = self._target.getSession()
        if session!=None:
            x.writeTag("Session", self._target.getSession().getTitle())
        l = []
        for au in self._target.getAuthorList():
            if self._target.isPrimaryAuthor(au):
                x.openTag("PrimaryAuthor")
                x.writeTag("FirstName", au.getFirstName())
                x.writeTag("FamilyName", au.getFamilyName())
                x.writeTag("Email", au.getEmail())
                #x.writeTag("Affiliation", au.getAffiliation())
                x.closeTag("PrimaryAuthor")
            else:
                l.append(au)
        
        for au in l:
            x.openTag("Co-Author")
            x.writeTag("FirstName", au.getFirstName())
            x.writeTag("FamilyName", au.getFamilyName())
            x.writeTag("Email", au.getEmail())
            #x.writeTag("Affiliation", au.getAffiliation())
            x.closeTag("Co-Author") 
        
        for au in self._target.getSpeakerList():
            x.openTag("Speaker")
            x.writeTag("FirstName", au.getFirstName ())
            x.writeTag("FamilyName", au.getFamilyName())
            x.writeTag("Email", au.getEmail())
            #x.writeTag("Affiliation", au.getAffiliation())
            x.closeTag("Speaker")
        
        #To change for the new contribution type system to:
        x.writeTag("ContributionType", self._target.getType())
        
        t = self._target.getTrack()
        if t!=None:
            x.writeTag("Track", t.getTitle())
        
        x.closeTag("contribution")
        
        data = x.getXml()
        
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType("XML")
        self._req.content_type = """%s"""%(mimetype)
        self._req.headers_out["Content-Length"] = "%s"%len(data)
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
        return data


class RHContributionToPDF(RHContributionModification):
    _uh = urlHandlers.UHContribToPDFConfManager
    
    def _process(self):
        tz = self._target.getConference().getTimezone()
        filename = "%s - Contribution.pdf"%self._target.getTitle()
        pdf = ConfManagerContribToPDF(self._target.getConference(), self._target, tz=tz)
        data = pdf.getPDFBin()
        self._req.headers_out["Content-Length"] = "%s"%len(data)
        cfg = Config.getInstance()
        mimetype = cfg.getFileTypeMimeType("PDF")
        self._req.content_type = """%s"""%(mimetype)
        self._req.headers_out["Content-Disposition"] = """inline; filename="%s\""""%filename
        return data


class RHAuthBase(RHContribModifBaseSpecialSesCoordRights):

    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        self._auth=self._target.getAuthorById(params.get("authId", ""))


class RHPrimAuthUp(RHAuthBase):
    
    def _process(self):
        contrib=self._target
        contrib.upPrimaryAuthor(self._auth)
        self._redirect(urlHandlers.UHContributionModification.getURL(contrib))


class RHPrimAuthDown(RHAuthBase):
    
    def _process(self):
        contrib=self._target
        contrib.downPrimaryAuthor(self._auth)
        self._redirect(urlHandlers.UHContributionModification.getURL(contrib))


class RHCoAuthUp(RHAuthBase):
    
    def _process(self):
        contrib=self._target
        contrib.upCoAuthor(self._auth)
        self._redirect(urlHandlers.UHContributionModification.getURL(contrib))


class RHCoAuthDown(RHAuthBase):
    
    def _process(self):
        contrib=self._target
        contrib.downCoAuthor(self._auth)
        self._redirect(urlHandlers.UHContributionModification.getURL(contrib))

class RHNewSpeaker(RHContribModifBaseSpecialSesCoordRights):
    
    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        self._action=""
        if params.has_key("ok"):
            self._action = "perform"
        elif params.has_key("cancel"):
            self._action = "cancel"

    def _newSpeaker(self):
        auth = conference.ContributionParticipation()
        p = self._getRequestParams()
        auth.setTitle(p.get("title", ""))
        auth.setFirstName(p.get("name", ""))
        auth.setFamilyName(p.get("surName", ""))
        auth.setAffiliation(p.get("affiliation", ""))
        auth.setEmail(p.get("email", ""))
        auth.setAddress(p.get("address", ""))
        auth.setPhone(p.get("phone", ""))
        auth.setFax(p.get("fax", ""))
        self._target.newSpeaker(auth)
        return auth
    
    def _process(self):
        if self._action != "":
            if self._action == "perform":
                auth=self._newSpeaker()
                if self._getRequestParams().has_key("submissionControl"):
                    if self._getRequestParams().get("email", "").strip() != "":
                        #raise FormValuesError("If you want to add the author as submitter, please enter their email")
                        self._target.grantSubmission(auth)
            url=urlHandlers.UHContributionModification.getURL(self._target)
            self._redirect(url)
        else:
            p = contributions.WPModNewSpeaker(self, self._target)
            wf = self.getWebFactory()
            if wf != None:
                p = wf.getContributionNewspeaker(self, self._target)
            return p.display()

class RHEditSpeaker(RHContribModifBaseSpecialSesCoordRights):
    
    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        self._authorId=params["authorId"]
        self._action=""
        if params.has_key("ok"):
            self._action = "perform"
        elif params.has_key("cancel"):
            self._action = "cancel"

    def _setSpeakerData(self):
        auth=self._target.getSpeakerById(self._authorId)
        if auth is not None:
            p = self._getRequestParams()
            auth.setTitle(p.get("title", ""))
            auth.setFirstName(p.get("name", ""))
            auth.setFamilyName(p.get("surName", ""))
            auth.setAffiliation(p.get("affiliation", ""))
            auth.setAddress(p.get("address", ""))
            auth.setPhone(p.get("phone", ""))
            auth.setFax(p.get("fax", ""))
            
            grantSubm=False
            if auth.getEmail().lower().strip() != p.get("email", "").lower().strip():
                #----If it's already in the pending queue in order to grant 
                #    submission rights we must unindex and after the modification of the email,
                #    index again...
                if self._target.getConference().getPendingQueuesMgr().isPendingSubmitter(auth):
                    self._target.getConference().getPendingQueuesMgr().removePendingSubmitter(auth)
                    grantSubm=True
                #-----
            
            auth.setEmail(p.get("email", ""))

            if grantSubm:
                if p.get("email", "").strip() == "":
                    raise FormValuesError("This speaker is in a pending queue waiting to become submitter therefore the email address cannot be empty, please enter their email")
                self._target.grantSubmission(auth)
            elif p.has_key("submissionControl"):
                if p.get("email", "").strip() == "":
                    raise FormValuesError("If you want to add the speaker as submitter, please enter their email")
                self._target.grantSubmission(auth)
    
    def _process(self):
        if self._action != "":
            if self._action == "perform":
                self._setSpeakerData()
            url=urlHandlers.UHContributionModification.getURL(self._target)
            self._redirect(url)
        else:
            auth=self._target.getSpeakerById(self._authorId)
            p = contributions.WPModSpeaker(self, self._target)
            wf = self.getWebFactory()
            if wf != None:
                p = wf.getModSpeaker(self, self._target)
            return p.display(author=auth)


class RHSubmittersRem(RHContribModifBaseSpecialSesCoordRights):
    _uh=urlHandlers.UHContribModSubmittersRem

    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        self._submitters=[]
        self._pendings=[]
        ah=user.PrincipalHolder()
        for id in self._normaliseListParam(params.get("selUsers", [])):
            av=ah.getById(id)
            if av is None:
                self._pendings.append(id)
            else:
                self._submitters.append(av)
    
    def _process(self):
        for sub in self._submitters:
            self._target.revokeSubmission(sub)
        for email in self._pendings:
            self._target.revokeSubmissionEmail(email)
        self._redirect(urlHandlers.UHContribModifAC.getURL(self._target))


class RHSubmittersSel(RHContribModifBaseSpecialSesCoordRights):
    _uh=urlHandlers.UHContribModSubmittersSel
    
    def _process(self):
        p=contributions.WPModSubmittersSel(self, self._target)
        return p.display(**self._getRequestParams())


class RHSubmittersAdd(RHContribModifBaseSpecialSesCoordRights):
    _uh=urlHandlers.UHContribModSubmittersAdd

    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordRights._checkParams(self, params)
        self._submitterRole=self._normaliseListParam(params.get("submitterRole", []))
    
    def _process(self):
        params=self._getRequestParams()
        if "selectedPrincipals" in params:
            ah=user.PrincipalHolder()
            for id in self._normaliseListParam(params["selectedPrincipals"]):
                av=ah.getById(id)
                self._target.grantSubmission(av)
                if self._submitterRole!=[] and not isinstance(av, user.Group):
                    cp=conference.ContributionParticipation()
                    cp.setDataFromAvatar(av)
                    if "primaryAuthor" in self._submitterRole:
                        self._target.addPrimaryAuthor(cp)
                    elif "coAuthor" in self._submitterRole:
                        self._target.addCoAuthor(cp)
                    if "speaker" in self._submitterRole:
                        if self._submitterRole in ["primaryAuthor", "coAuthor"]:
                            self._target.addSpeaker(cp)
                        else:
                            self._target.newSpeaker(cp)
        self._redirect(urlHandlers.UHContribModifAC.getURL(self._target))

class RHMaterials(RHContribModifBaseSpecialSesCoordAndReviewingStaffRights):
    _uh = urlHandlers.UHContribModifMaterials
    
    def _checkProtection(self):
        """ This disables people that are not conference managers or track coordinators to
            delete files from a contribution.
        """
        RHContribModifBaseSpecialSesCoordAndReviewingStaffRights._checkProtection(self)
        for key in self._paramsForCheckProtection.keys():
            if key.find("delete")!=-1:
                RHContribModifBaseSpecialSesCoordRights._checkProtection(self)
    
    def _checkParams(self, params):
        RHContribModifBaseSpecialSesCoordAndReviewingStaffRights._checkParams(self, params)
        if not hasattr(self, "_rhSubmitMaterial"):
            self._rhSubmitMaterial=RHSubmitMaterialBase(self._target, self)
        self._rhSubmitMaterial._checkParams(params)
        params["days"] = params.get("day", "all")
        if params.get("day", None) is not None :
            del params["day"]
        # note from DavidMC: i wrote this long parameter name in order
        # not to overwrite a possibly existing _params in a base class
        # we need to store the params so that _checkProtection can know
        # if the action is to upload a file, delete etc. 
        self._paramsForCheckProtection = params
    
    def _process(self):
        if self._target.getOwner().isClosed():
            p = WPConferenceModificationClosed( self, self._target )
            return p.display()

        p = contributions.WPContributionModifMaterials( self, self._target )
        return p.display(**self._getRequestParams())

        

class RHContributionReportNumberEdit(RHContribModifBase):

    def _checkParams(self, params):
        RHContribModifBase._checkParams(self, params)
        self._reportNumberSystem=params.get("reportNumberSystem","")
        
    def _process(self):
        if self._reportNumberSystem!="":
            p=contributions.WPContributionReportNumberEdit(self,self._target, self._reportNumberSystem)
            return p.display()
        else:
            self._redirect(urlHandlers.UHContributionModification.getURL( self._target ))

class RHContributionReportNumberPerformEdit(RHContribModifBase):

    def _checkParams(self, params):
        RHContribModifBase._checkParams(self, params)
        self._reportNumberSystem=params.get("reportNumberSystem","")
        self._reportNumber=params.get("reportNumber","")
        
    def _process(self):
        if self._reportNumberSystem!="" and self._reportNumber!="":
            self._target.getReportNumberHolder().addReportNumber(self._reportNumberSystem, self._reportNumber)
        self._redirect("%s#reportNumber"%urlHandlers.UHContributionModification.getURL( self._target ))


class RHContributionReportNumberRemove(RHContribModifBase):

    def _checkParams(self, params):
        RHContribModifBase._checkParams(self, params)
        self._reportNumberIdsToBeDeleted=self._normaliseListParam( params.get("deleteReportNumber",[]))
        
    def _process(self):
        nbDeleted = 0
        for id in self._reportNumberIdsToBeDeleted:
            self._target.getReportNumberHolder().removeReportNumberById(int(id)-nbDeleted)
            nbDeleted += 1
        self._redirect("%s#reportNumber"%urlHandlers.UHContributionModification.getURL( self._target ))



