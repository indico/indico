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

from copy import copy
from datetime import timedelta, datetime
import MaKaC.webinterface.rh.base as base
import MaKaC.webinterface.locators as locators
import MaKaC.webinterface.webFactoryRegistry as webFactoryRegistry
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.pages.tasks as tasks
import MaKaC.webinterface.pages.category as category
from MaKaC.errors import MaKaCError
from MaKaC.common.Configuration import Config
from MaKaC.webinterface.rh.categoryDisplay import RHCategDisplayBase
import MaKaC.user as user
from MaKaC.task import TaskStatus
from MaKaC.task import TaskComment
from MaKaC.conference import ContributionParticipation
from MaKaC.i18n import _

class RHTaskModifBase(RHCategDisplayBase):

    def _checkProtection( self ):
        if self._getUser() == None:
            self._checkSessionUser()
        else:
            RHCategDisplayBase._checkProtection(self)

class RHTaskList( RHCategDisplayBase ):
    _uh = urlHandlers.UHTaskList
    
    def _process( self ):        
        params = self._getRequestParams()
        order = params.get("order","1")
        p = tasks.WPTaskList( self, self._target,"", order)
        return p.display()


#---------------------------------------------------------------

class RHTaskListAction( RHCategDisplayBase ):
    _uh = urlHandlers.UHTaskListAction
    
    def _process( self ):        
        params = self._getRequestParams()
        
        if params.get("actionPerformed",None) is None :
            p = tasks.WPTaskList( self, self._target)
            return p.display()
        if params["actionPerformed"] == _("New task") :
            url = urlHandlers.UHTaskNew.getURL(self._target)
            url.addParam("clear","true")
            self._redirect(url)
            return     
        if params["actionPerformed"] == _("Apply filter") :            
            filter = params.get("filter","")
            p = tasks.WPTaskList( self, self._target, filter)
            return p.display()

        p = tasks.WPTaskList( self, self._target)
        return p.display()

#--------------------------------------------------------------------------

class RHTaskNew( RHTaskModifBase ):
    _uh = urlHandlers.UHTaskNew
    
    
    def _checkParams( self, params):
        RHTaskModifBase._checkParams(self,params)
        if params.get("clear",None) is not None :
            self._removeDefinedList("responsible")
            self._removePreservedParams()
            del params["clear"]
    
    def _process( self ):        
        preservedParams = self._getPreservedParams()
        params = self._getRequestParams()
        params.update(preservedParams)
        params["createdBy"] = self._getUser().getFullName()
        params["creatorId"] = self._getUser().getId()
        
        params = copy(params)
        
        params["responsibleOptions"] = self._getResponsibleOptions()
        params["responsibleDefined"] = self._getDefinedList("responsible",False)
        
        p = tasks.WPTaskNew( self, self._target, params)
        return p.display()

    def _getPreservedParams(self):
        params = self._websession.getVar("preservedParams")
        if params is None :
            return {}
        return params

    def _getResponsibleOptions(self): 
        html = []        
        for t in self._target.getTaskList() :
            index = 0
            for resp in t.getResponsibleList() :
                text = """<option value="%s-%s">%s</option>"""%(t.getId(),index,resp.getFullName())
                html.append(text)
        return """
                """.join(html)
    
    def _getDefinedList(self, typeName, submission):
        lis = self._websession.getVar("%sList"%typeName)
        if lis is None :
            return ""
        
        html = []
        counter = 0
        for person in lis :
            subm = ""
            if submission and person[1] :
                subm = _("""<td> _("submiter")</td>""")
                
            text = """
                <tr>
                    <td width="5%%"><input type="checkbox" name="%ss" value="%s"></td>
                    <td width="100%%">&nbsp;%s</td>
                    %s
                </tr>"""%(typeName,counter,person[0].getFullName(),subm)
            html.append(text)
            counter = counter + 1
        return """
            """.join(html)
    
    def _removeDefinedList(self, typeName):
        self._websession.setVar("%sList"%typeName,None)
        
    def _removePreservedParams(self):
        self._websession.setVar("preservedParams",None)
    
    def _personInDefinedList(self, typeName, person):    
        lis = self._websession.getVar("%sList"%typeName)
        if lis is None :
            return False
        for p in lis :
            if person.getFullName()+" "+person.getEmail() == p[0].getFullName()+" "+p[0].getEmail() :
                return True
        return False
    
#---------------------------------------------------------------

class RHTaskNewAdd( RHTaskModifBase ):
    _uh = urlHandlers.UHTaskNewAdd
    
    
    def _process( self ):        
        params = self._getRequestParams()

        #raise  "%s"%params
        if params.get("performedAction","") == "Add as responsible" :
            self._preserveParams()
            url = urlHandlers.UHTaskNewPersonAdd.getURL(self._target)
            url.addParam("orgin","added")
            url.addParam("typeName","responsible")
            self._redirect(url)   
            return
        if params.get("performedAction","") == "New responsible" :
            self._preserveParams()
            url = urlHandlers.UHTaskNewResponsibleNew.getURL(self._target)
            url.addParam("eventType",params.get("eventType","conference"))
            self._redirect(url)
            return
        if params.get("performedAction","") == "Search responsible" :
            self._preserveParams()
            url = urlHandlers.UHTaskNewResponsibleSearch.getURL(self._target)
            url.addParam("eventType",params.get("eventType","conference"))
            self._redirect(url)
            return
        if params.get("performedAction","") == "Remove responsibles" :
            self._removePersons(params, "responsible")
            
            self._redirect(urlHandlers.UHTaskNew.getURL(self._target))
            return
        if params.has_key("cancel") :
            self._removePreservedParams()
            self._removeDefinedList("responsible")            
        if params.get("performedAction","") == _("ok") :
            task = self._target.newTask(self._getUser())
            task.setTitle(params.get("title",""))
            task.setDescription(params.get("taskDescription",""))
            #adding responsible persons
            responsibleList = self._getDefinedList("responsible")
            for responsible in responsibleList :
                task.addResponsible(responsible[0])
            
            self._removePreservedParams()
            self._removeDefinedList("responsible")            
            
        self._redirect(urlHandlers.UHTaskList.getURL(self._target))


    def _preserveParams(self):
        preservedParams = self._getRequestParams().copy()
        self._websession.setVar("preservedParams",preservedParams)
    
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
   
#--------------------------------------------------------------------------

class RHTaskNewResponsibleSearch( RHTaskModifBase ):
    _uh = urlHandlers.UHTaskNewResponsibleSearch

    def _checkParams( self, params):
        RHTaskModifBase._checkParams(self,params)
        
    def _process( self ):
        params = self._getRequestParams()
        
        params["newButtonAction"] = str(urlHandlers.UHTaskNewResponsibleNew.getURL())
        addURL = urlHandlers.UHTaskNewPersonAdd.getURL()
        addURL.addParam("orgin","selected")
        addURL.addParam("typeName","responsible")
        params["addURL"] = addURL
        p = tasks.WPTaskNewResponsibleSelect( self, self._target)
        return p.display(**params)
   
#-------------------------------------------------------------------------------------

class RHTaskNewPersonAdd( RHTaskModifBase ):
    _uh = urlHandlers.UHTaskNewPersonAdd

    def _checkParams( self, params):
        RHTaskModifBase._checkParams(self,params)
        self._typeName = params.get("typeName",None)
        if self._typeName  is None :
            raise MaKaCError( _("Type name of the person to add is not set."))
        
    def _process( self ):
        params = self._getRequestParams()
        self._errorList = []
        
        #raise "%s"%params
        definedList = self._getDefinedList(self._typeName)
        if definedList is None :
            definedList = []
        
        if params.get("orgin","") == "new" :
            #raise "new"
            if params.get("ok",None) is None :
                raise "not ok"
                self._redirect(urlHandlers.UHTaskNew.getURL(self._target))
                return
            else :                
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
                    definedList.append([person,params.has_key("submissionControl")])    
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
            taskId = chosen[0:index]
            resId = chosen[index+1:len(chosen)]
            taskObject = self._target.getTask(taskId)
            chosenPerson = taskObject.getResponsibleList()[int(resId)]
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
        
        self._redirect(urlHandlers.UHTaskNew.getURL(self._target))


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

class RHTaskNewResponsibleNew( RHTaskModifBase ):
    _uh = urlHandlers.UHTaskNewResponsibleNew

    def _checkParams( self, params):
        RHTaskModifBase._checkParams(self,params)
        
    def _process( self ):
        p = tasks.WPTaskNewResponsibleNew( self, self._target)
        return p.display()


#--------------------------------------------------------------------------

class RHTaskDetails( RHCategDisplayBase ):
    _uh = urlHandlers.UHTaskDetails
    
    def _process( self ):        
        params = self._getRequestParams()
        if params.get("taskId",None) is None :
            raise MaKaCError( _("Task id is not set - cannot display task details"))
        user = self._getUser()
        task = self._target.getTask(params["taskId"])
        emails = []
        for r in task.getResponsibleList() :
            emails.append(r.getEmail())
        if user is None :
            params["editRights"] = "False"
        elif self._target.canUserModify(user) :
            params["editRights"] = "True"
        elif user in task.getResponsibleList() or user.getEmail() in emails :
            params["editRights"] = "True"
        else :             
            params["editRights"] = "False"
        
        p = tasks.WPTaskDetails( self, task, params)
        return p.display()

        
class RHTaskDetailsAction( RHCategDisplayBase ):
    _uh = urlHandlers.UHTaskDetailsAction
    
    def _process( self ):        
        params = self._getRequestParams()
        
        #raise "%s"%params
        if params.get("taskId",None) is None :
            raise MaKaCError( _("Task id is not set - cannot preform task details action"))
        elif isinstance(params.get("taskId"),list):
            params["taskId"]=params.get("taskId")[0]
        task = self._target.getTask(params["taskId"])
        if params.get("performedAction",None ) is None :
            p = tasks.WPTaskDetails( self, task, params)
            return p.display()
        if params.get("performedAction","") == _("Show comments list") :
            params["showComments"] = "true"
        if params.get("performedAction","") == _("Hide comments list") :
            del params["showComments"]
        
        if params.get("performedAction","") == _("Show status history") :
            params["showStatus"] = "true"
        if params.get("performedAction","") == _("Hide status history") :
            del params["showStatus"]
        
        if params.get("performedAction","") == _("Change status") :
            status = TaskStatus(params["changedStatus"],self._getUser())
            task.changeStatus(status)
            params["showStatus"] = "true"
        
        if params.get("performedAction","") == "Add as responsible" :
            resId = params.get("responsibleChosen",None)
            if resId is not None :
                index = resId.find("-")
                taskId = resId[0:index]
                resId = resId[index+1:]
                responsible = self._target.getTask(taskId).getResponsibleList()[int(resId)]
                task.addResponsible(responsible)
                
        if params.get("performedAction","") == "Remove responsibles" :
            toRemove = self._normaliseListParam(params.get("responsibles",[]))
            if len(toRemove) > 0 :
                lis = []
                for i in toRemove :
                    lis.append(task.getResponsibleList()[int(i)])
                for r in lis :
                    task.removeResponsible(r)
        if params.get("performedAction","") == "New responsible" :
            url = urlHandlers.UHTaskDetailsResponsibleSearch.getURL(task)  
            url.addParam("taskId",params["taskId"])
            self._redirect(url)
            return
                    
        if params.get("performedAction","") == "New comment" :
            url = urlHandlers.UHTaskCommentNew.getURL(task)
            url.addParam("taskId",params["taskId"])
            self._redirect(url)
            return
                    
        
        p = tasks.WPTaskDetails( self, task, params)
        return p.display()

#--------------------------------------------------------------------------

class RHTaskDetailsResponsibleSearch( RHCategDisplayBase ):
    _uh = urlHandlers.UHTaskDetailsResponsibleSearch

    def _checkParams( self, params):
        RHCategDisplayBase._checkParams(self,params)
        
    def _process( self ):
        params = self._getRequestParams()
        
        params["newButtonAction"] = str(urlHandlers.UHTaskDetailsResponsibleNew.getURL())
        addURL = urlHandlers.UHTaskDetailsPersonAdd.getURL()
        addURL.addParam("orgin","selected")
        addURL.addParam("typeName","responsible")
        #addURL.addParam("taskId",params["taskId"])
        params["addURL"] = addURL
        
        p = tasks.WPTaskDetailsResponsibleSelect( self, self._target)
        return p.display(**params)
   
#-------------------------------------------------------------------------------------

class RHTaskDetailsPersonAdd( RHTaskModifBase ):
    _uh = urlHandlers.UHTaskDetailsPersonAdd

    def _checkParams( self, params):
        RHTaskModifBase._checkParams(self,params)
        self._typeName = params.get("typeName",None)
        if self._typeName  is None :
            raise MaKaCError( _("Type name of the person to add is not set."))
        
    def _process( self ):
        params = self._getRequestParams()
        self._errorList = []
        
        #raise "%s"%params
        taskId = params["taskId"]

        taskObject = self._target.getTask(taskId)
        if params.get("orgin","") == "new" :            
            if params.get("ok",None) is None :
                raise "not ok"
                url = urlHandlers.UHTaskDetails.getURL(self._target)
                url.addParam("taskId",params["taskId"])
                self._redirect(url)
                return
            else :                
                person = ContributionParticipation()
                person.setFirstName(params["name"])
                person.setFamilyName(params["surName"])
                person.setEmail(params["email"])
                person.setAffiliation(params["affiliation"])
                person.setAddress(params["address"])
                person.setPhone(params["phone"])
                person.setTitle(params["title"])
                person.setFax(params["fax"])                
                if not self._alreadyDefined(person, taskObject.getResponsibleList()) :                    
                    taskObject.addResponsible(person)
                else :
                    self._errorList.append("%s has been already defined as %s of this task"%(person.getFullName(),self._typeName))
        
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
                    if not self._alreadyDefined(person, taskObject.getResponsibleList()) :                    
                        taskObject.addResponsible(person)
                    else :
                        self._errorList.append("%s has been already defined as %s of this task"%(person.getFullName(),self._typeName))
                        
                elif isinstance(selected, user.Group) : 
                    for member in selected.getMemberList() :
                        person = ContributionParticipation()
                        person.setDataFromAvatar(member)
                        if not self._alreadyDefined(person, taskObject.getResponsibleList()) :                    
                            taskObject.addResponsible(person)
                        else :
                            self._errorList.append("%s has been already defined as %s of this task"%(person.getFullName(),self._typeName))
                        
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
                    if not self._alreadyDefined(person, taskObject.getResponsibleList()) :                    
                        taskObject.addResponsible(person)
                    else :
                        self._errorList.append("%s has been already defined as %s of this task"%(person.getFullName(),self._typeName))
            else :
                url = urlHandlers.UHTaskDetails.getURL(self._target)
                url.addParam("taskId",params["taskId"])
                self._redirect(url)
                return
        
        url = urlHandlers.UHTaskDetails.getURL(self._target)
        url.addParam("taskId",params["taskId"])
        self._redirect(url)

    def _alreadyDefined(self, person, definedList):
        if person is None :
            return True
        if definedList is None :
            return False
        fullName = person.getFullName()
        for p in definedList :
            if p.getFullName() == fullName :
                return True
        return False

#-------------------------------------------------------------------------------------

class RHTaskDetailsResponsibleNew( RHTaskModifBase ):
    _uh = urlHandlers.UHTaskNewResponsibleNew

    def _checkParams( self, params):
        RHTaskModifBase._checkParams(self,params)
        
    def _process( self ):
        params = self._getRequestParams()
        p = tasks.WPTaskDetailsResponsibleNew( self, self._target, params)
        return p.display()
        
        
#--------------------------------------------------------------------------

class RHTaskCommentNew( RHTaskModifBase ):
    _uh = urlHandlers.UHTaskCommentNew
    
    def _process( self ):        
        params = self._getRequestParams()
        if params.get("taskId",None) is None :
            raise MaKaCError( _("Task id is not set - cannot add a comment"))
            
        params["commentedBy"] = self._getUser().getFullName()
        
        p = tasks.WPTaskCommentNew( self, self._target, params)
        return p.display()


class RHTaskCommentNewAction( RHTaskModifBase ):
    _uh = urlHandlers.UHTaskCommentNewAction
    
    def _process( self ):        
        params = self._getRequestParams()
        if params.get("taskId",None) is None :
            raise MaKaCError( _("Task id is not set - cannot add a comment"))
                    
        task = self._target.getTask(params["taskId"])            
        if params.get("performedAction","") == "ok" :
            task.addComment(self._getUser(),params["commentText"])
        
        url = urlHandlers.UHTaskDetails().getURL(task)
        url.addParam("showComments", "true")
        self._redirect(url)

        
