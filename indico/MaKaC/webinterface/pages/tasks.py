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

import os
from pytz import timezone

import MaKaC.webinterface.pages.main as main
import MaKaC.webinterface.urlHandlers as urlHandlers
import MaKaC.webinterface.wcomponents as wcomponents
import MaKaC.conference as conference
import MaKaC.task as task
from MaKaC.conference import CategoryManager
from MaKaC.common.Configuration import Config
from MaKaC.webinterface.pages.category import WPCategoryDisplayBase
from MaKaC.i18n import _
from MaKaC.common.timezoneUtils import DisplayTZ


class WTaskList(wcomponents.WTemplated):
        
    def __init__( self, aw, target, filter="", order="1"):
        self._target = target
        self._taskFilter = filter
        self._listOrder = order
        self._aw = aw

    def getHTML( self, params ):        
        return wcomponents.WTemplated.getHTML( self, params )
    
    def getVars( self ):
        vars = wcomponents.WTemplated.getVars( self )
        vars["name"] = self._target.getName()
        vars["img"] = Config.getInstance().getSystemIconURL( "category" )
        vars["description"] = "&nbsp;"  
        vars["conferenceList"] = urlHandlers.UHCategoryDisplay.getURL(self._target)  
        vars["contents"] = self._getTaskList()  
        
        idURL = urlHandlers.UHTaskList.getURL(self._target)
        idURL.addParam("order","1")
        vars["idURL"] = idURL
        titleURL = urlHandlers.UHTaskList.getURL(self._target)
        titleURL.addParam("order","2")
        vars["titleURL"] = titleURL
        statusURL = urlHandlers.UHTaskList.getURL(self._target)
        statusURL.addParam("order","3")
        vars["statusURL"] = statusURL
        dateURL = urlHandlers.UHTaskList.getURL(self._target)
        dateURL.addParam("order","4")
        vars["dateURL"] = dateURL
        
        vars["taskManagementAction"] = urlHandlers.UHTaskListAction.getURL(self._target)
        
        filterOptions = []
        filterOptions.append("<option></option>")
        for s in task.statusList :
            filterOptions.append("<option>%s</option>"%_(s))
        vars["filterOptions"] = """
                """.join(filterOptions)
        
        mgrs=[]
        from MaKaC.user import Avatar
        for mgr in self._target.getManagerList():
            if isinstance(mgr, Avatar):
               mgrs.append(mgr.getAbrName())
        vars["managers"]=""
        if mgrs != []:
            vars["managers"]= _("""(<b> _("Managers")</b>: %s)""")%"; ".join(mgrs)
        return vars

    def _getTaskList(self):
        html = []
        
        taskList = self._target.getTaskList()[:]
        if self._listOrder == "1" :
            taskList.sort(task.Task.cmpTaskId)
        if self._listOrder == "2" :
            taskList.sort(task.Task.cmpTaskTitle)            
        if self._listOrder == "3" :
            taskList.sort(task.Task.cmpTaskCurrentStatus)            
        if self._listOrder == "4" :
            taskList.sort(task.Task.cmpTaskCreationDate)                    
            
        for t in taskList :
            if self._taskFilter == "" or self._taskFilter == t.getCurrentStatus().getStatusName() :
                urlDetails = urlHandlers.UHTaskDetails.getURL(self._target)
                urlDetails.addParam("taskId",t.getId())
                urlComment = urlHandlers.UHTaskCommentNew.getURL(self._target)
                urlComment.addParam("taskId",t.getId())
                tz = DisplayTZ(self._aw,None,useServerTZ=1).getDisplayTZ()
                creationDate = "%s"%t.getCreationDate().astimezone(timezone(tz))
                text = _("""
                <tr>
                    <td>&nbsp;&nbsp;%s</td>
                    <td>&nbsp;&nbsp;<a href="%s">%s</a></td>
                    <td>&nbsp;&nbsp;%s</td>
                    <td>&nbsp;&nbsp;%s</td>
                    <td align="center">&nbsp;&nbsp;%s</td>
                    <td align="center"><a href="%s"> _("comment")</a></td>
                </tr>
                """)%(t.getId(),urlDetails,t.getTitle(), _(t.getCurrentStatus().getStatusName()), creationDate[0:16], t.getCommentHistorySize(),urlComment)
                html.append(text)
            
        return """
        """.join(html)

class WPTaskList( WPCategoryDisplayBase ):
    
    def __init__( self, rh, target, filter="", order="1" ):
        WPCategoryDisplayBase.__init__( self, rh, target )
        self._taskFilter = filter
        self._listOrder = order
        if len(self._target.getSubCategoryList())==0:
            tzUtil = DisplayTZ(self._getAW(),None,useServerTZ=1) 
            self._locTZ = tzUtil.getDisplayTZ() 
        
    def _getBody( self, params ):
        wc = WTaskList( self._getAW(), self._target, self._taskFilter, self._listOrder )
        pars = { "categDisplayURLGen": urlHandlers.UHCategoryDisplay.getURL, \
                "confDisplayURLGen": urlHandlers.UHConferenceDisplay.getURL }
        return wc.getHTML( pars )
        
    def _getNavigationDrawer(self):
        pars = {"target": self._target, "isModif": False}
        return wcomponents.WNavigationDrawer( pars )

#------------------------------------------------------------------------------

class WTaskNew(wcomponents.WTemplated):
        
    def __init__( self, target):
        self._target = target

    def getHTML( self, params ):        
        return wcomponents.WTemplated.getHTML( self, params )
    
    def getVars( self ):        
        vars = wcomponents.WTemplated.getVars( self )
        
        vars["name"] = self._target.getName()
        vars["img"] = Config.getInstance().getSystemIconURL( "category" )
        vars["description"] = "&nbsp;"  
        vars["conferenceList"] = urlHandlers.UHCategoryDisplay.getURL(self._target)  
        vars["taskDetailsTitle"] = vars.get("taskDetailsTitle", _("Task Details"))        
        vars["taskDetailsAction"] = vars.get("taskDetailsAction","")        
        vars["title"] = vars.get("title","")
        vars["taskDescription"] = vars.get("taskDescription","")
        if vars.get("id", None) is not None :
            vars["id"] = _("""
            <tr>
                <td nowrap class="titleCellTD"><span class="titleCellFormat">
                    _("Id")
                </span></td>
                <td>%s</td>
            </tr>""")%vars["id"]
        else :
            vars["id"] = ""
            
        mgrs=[]
        from MaKaC.user import Avatar
        for mgr in self._target.getManagerList():
            if isinstance(mgr, Avatar):
               mgrs.append(mgr.getAbrName())
        vars["managers"]=""
        if mgrs != []:
            vars["managers"]= _("""(<b> _("Managers")</b>: %s)""")%"; ".join(mgrs)
        
        vars["responsibleDefined"] = vars.get("responsibleDefined","")
        vars["responsibleOptions"] = vars.get("responsibleOptions","")
        wresponsible = wcomponents.WAddPersonModule("responsible")
        vars["responsible"] = wresponsible.getHTML(vars)
            
        return vars

#------------------------------------------------------------------------------

class WPTaskNew( WPCategoryDisplayBase ):
    
    def __init__( self, rh, target, params ):
        WPCategoryDisplayBase.__init__( self, rh, target )
        self._params = params
    
    def _getBody( self, params ):
        
        wc = WTaskNew( self._target )
        pars = { "categDisplayURLGen": urlHandlers.UHCategoryDisplay.getURL, \
                "confDisplayURLGen": urlHandlers.UHConferenceDisplay.getURL }
        params.update(pars)
        params.update(self._params)
        params["taskDetailsTitle"] = _("New task")
        params["taskDetailsAction"] = urlHandlers.UHTaskNewAdd.getURL(self._target)
        
        return wc.getHTML( params )
        
    def _getNavigationDrawer(self):
        pars = {"target": self._target, "isModif": False}
        return wcomponents.WNavigationDrawer( pars )

#---------------------------------------------------------------------------

class WPTaskNewResponsibleSelect( WPCategoryDisplayBase ):
    
        
    def _getBody( self, params ):
        url = self._rh.getCurrentURL()
        searchAction = str(url)
        p = wcomponents.WCategoryComplexSelection(self._target,searchAction)
        return p.getHTML(params)

#---------------------------------------------------------------------------

class WPTaskNewResponsibleNew( WPCategoryDisplayBase ):
    
    def _getBody( self, params ):
        p = wcomponents.WNewPerson()
        
        if params.get("formTitle",None) is None :
            params["formTitle"] = _("Define new responsible")
        if params.get("titleValue",None) is None :
            params["titleValue"] = ""
        if params.get("surNameValue",None) is None :
            params["surNameValue"] = ""
        if params.get("nameValue",None) is None :
            params["nameValue"] = ""
        if params.get("emailValue",None) is None :
            params["emailValue"] = ""
        if params.get("addressValue",None) is None :
            params["addressValue"] = ""
        if params.get("affiliationValue",None) is None :
            params["affiliationValue"] = ""
        if params.get("phoneValue",None) is None :
            params["phoneValue"] = ""
        if params.get("faxValue",None) is None :
            params["faxValue"] = ""
        
        params["disabledSubmission"] = False
        params["submissionValue"] = _(""" <input type="checkbox" name="submissionControl"> _("Give submission rights to the presenter").""")
        params["disabledNotice"] = False
        params["noticeValue"] = _("""<i><font color="black"><b>_("Note"): </b></font>_("If this person does not already have
         an Indico account, he or she will be sent an email asking to create an account. After the account creation the 
         user will automatically be given submission rights.")</i>""")
        
        formAction = urlHandlers.UHTaskNewPersonAdd.getURL(self._target)
        formAction.addParam("orgin","new")
        formAction.addParam("typeName","responsible")
        params["formAction"] = formAction
        
        return p.getHTML(params)

#---------------------------------------------------------------------------

#------------------------------------------------------------------------------

class WTaskDetails(wcomponents.WTemplated):
        
    def __init__( self, aw, target, editRights):
        self._aw = aw
        self._categ = target.getCategory()
        self._task = target
        self._editRights = editRights

    def getHTML( self, params ):        
        return wcomponents.WTemplated.getHTML( self, params )
    
    def getVars( self ):        
        vars = wcomponents.WTemplated.getVars( self )
        
        vars["name"] = self._categ.getName()
        vars["img"] = Config.getInstance().getSystemIconURL( "category" )
        vars["description"] = "&nbsp;"  
        vars["conferenceList"] = urlHandlers.UHCategoryDisplay.getURL(self._categ)  
        vars["taskList"] = urlHandlers.UHTaskList.getURL(self._categ)  
        vars["taskDetailsTitle"] = vars.get("taskDetailsTitle", _("Task Details"))        
        vars["taskDetailsAction"] = vars.get("taskDetailsAction","")        
            
        mgrs=[]
        from MaKaC.user import Avatar
        for mgr in self._categ.getManagerList():
            if isinstance(mgr, Avatar):
               mgrs.append(mgr.getAbrName())
        vars["managers"]=""
        if mgrs != []:
            vars["managers"]= _("""(<b> _("Managers")</b>: %s)""")%"; ".join(mgrs)
        
        vars["taskTitle"] = self._task.getTitle()
        vars["taskStatus"] = self._task.getCurrentStatus().getStatusName()
        vars["taskDescription"] = self._task.getDescription()
        vars["createdBy"] = self._task.getCreatedBy().getFullName()
        vars["creatorId"] = self._task.getCreatedBy().getId()
        
        if self._editRights :            
            vars["statusDisabled"] = ""
            vars["responsibleDefined"] = vars.get("responsibleDefined",self._getDefinedResponsible(self._task))
            vars["responsibleOptions"] = vars.get("responsibleOptions",self._getResponsibleOptions())
            wresponsible = wcomponents.WAddPersonModule("responsible")
            vars["responsible"] = wresponsible.getHTML(vars)    
        else : 
            vars["statusDisabled"] = "disabled"
            vars["responsible"] = _("""
            <tr>
                <td nowrap class="titleCellTD"><span class="titleCellFormat">
                    _("Responsible")
                </span></td>
                <td>%s</td>
            </tr>""")%self._getResponsibleList(self._task)
        
        taskStatusOptions = []     
        taskStatusList=task.statusList 
        statusIndex = taskStatusList.index(vars["taskStatus"])
        for i in range(len(taskStatusList)) :
            option = """<option value="%s">%s</option>"""%(taskStatusList[i], _(taskStatusList[i]))
            taskStatusOptions.append(option)
        vars["taskStatusOptions"] = """
                                """.join(taskStatusOptions)
    
        if vars.get("showComments",None) is None:
            vars["showCommentsButton"] = _("""<input type="submit" class="btn" name="performedAction" value="_("Show comments list")">""")
            vars["newCommentButton"] = _("""<input type="submit" class="btn" name="performedAction" value="_("New comment")">""")
            vars["commentsList"] = ""
            vars["showComments"] = ""
        else : 
            vars["showCommentsButton"] = _("""<input type="submit" class="btn" name="performedAction" value="_("Hide comments list")">""")
            vars["newCommentButton"] = _("""<input type="submit" class="btn" name="performedAction" value="_("New comment")">""")
            vars["commentsList"] = self._getCommentsList(self._task)            
            vars["showComments"] = """<input type="hidden" name="showComments" value="true">"""
        #raise "comments : >>%s<<"%vars["commentsList"]
        if vars.get("showStatus",None) is None :
            vars["showStatusButton"] = _("""<input type="submit" class="btn" name="performedAction" value="_("Show status history")">""")
            vars["statusList"] = ""
            vars["showStatus"] = ""
        else :
            vars["showStatusButton"] = _("""<input type="submit" class="btn" name="performedAction" value="_("Hide status history")">""")
            vars["statusList"] = self._getStatusList(self._task)
            vars["showStatus"] = """<input type="hidden" name="showStatus" value="true">"""
                
        vars["editRights"] = "%s"%self._editRights
        
        return vars

    def _getCommentsList(self, task):
        keys = task.getCommentHistory().keys()
        keys.sort()
        #raise "%s"%keys
        out = _("""
        <table width="100%">
            <tr>
                <td width="22%"><span class="titleCellFormat">&nbsp; _("Date")</span></td>
                <td width="50%"><span class="titleCellFormat">&nbsp; _("Text")</span></td>
                <td width="28%"><span class="titleCellFormat">&nbsp; _("Author")</span></td>
            </tr>""")
        html = []
        
        for k in keys :
            c = task.getCommentHistory()[k]
            tz = DisplayTZ(self._aw,None,useServerTZ=1).getDisplayTZ()
            date = "%s"%c.getCreationDate().astimezone(timezone(tz))
            text = """
            <tr>
                <td width="2%%">%s</td>
                <td width="50%%">%s</td>
                <td width="28%%">&nbsp;%s</td>
            </tr>"""%(date[0:16],c.getCommentText(),c.getCommentAuthor())
            html.append(text)
        
        return out + """
        """.join(html) + """
        </table>"""

    def _getStatusList(self, task):
        out = _("""
        <table width="100%">
            <tr>
                <td width="22%"><span class="titleCellFormat">&nbsp; _("Date")</span></td>
                <td width="50%"><span class="titleCellFormat">&nbsp; _("Status")</span></td>
                <td width="28%"><span class="titleCellFormat">&nbsp; _("Changed by")</span></td>
            </tr>""")
        html = []
        for s in task.getStatusHistoryEntries() :
            tz = DisplayTZ(self._aw,None,useServerTZ=1).getDisplayTZ()
            date = "%s"%s.getSettingDate().astimezone(timezone(tz))
            text = """
            <tr>
                <td>%s</td>
                <td>&nbsp;%s</td>
                <td>&nbsp;%s</td>
            </tr>
            """%(date[0:16], _(s.getStatusName()),s.getUserWhoSet().getFullName())
            html.append(text)

        return out + """
        """.join(html) + """
        </table>"""
        
    def _getResponsibleOptions(self): 
        html = []        
        for t in self._categ.getTaskList() :
            index = 0
            for resp in t.getResponsibleList() :
                text = """<option value="%s-%s">%s</option>"""%(t.getId(),index,resp.getFullName())
                html.append(text)
        return """
                """.join(html)
    
    def _getDefinedResponsible(self, task):
        html = []
        index = 0
        
        for r in task.getResponsibleList() :
            text = """
            <tr>
                <td><input type="checkbox" name="responsibles" value="%s"></td>
                <td>%s</td>
            </tr>"""%(index,r.getFullName())
            index = index + 1
            html.append(text)

        return """
            """.join(html)

    def _getResponsibleList(self, task) :
        html = []                
        for r in task.getResponsibleList() :            
            html.append(r.getFullName())

        return """, """.join(html)
        
    
            
class WPTaskDetails( WPCategoryDisplayBase ):
    
    def __init__( self, rh, target, params ):
        WPCategoryDisplayBase.__init__( self, rh, target.getCategory() )
        self._task = target
        self._params = params
        if len(self._target.getSubCategoryList())==0:
            tzUtil = DisplayTZ(self._getAW(),None,useServerTZ=1) 
            self._locTZ = tzUtil.getDisplayTZ() 
    
    def _getBody( self, params ):
        pars = { "categDisplayURLGen": urlHandlers.UHCategoryDisplay.getURL, \
                "confDisplayURLGen": urlHandlers.UHConferenceDisplay.getURL }        
        params.update(pars)
        params.update(self._params)        
        
        editRights = params.get("editRights", "False")
        
        if editRights == "True" :
            editRights = True
        else :
            editRights = False
            
        wc = WTaskDetails( self._getAW(), self._task, editRights )
        
        params["taskDetailsTitle"] = _("Task Details")
        url = urlHandlers.UHTaskDetailsAction.getURL(self._task)
        url.addParam("taskId",self._task.getId())
        params["taskDetailsAction"] = url
        return wc.getHTML( params )    
    
    
    def _getNavigationDrawer(self):
        pars = {"target": self._target, "isModif": False}
        return wcomponents.WNavigationDrawer( pars )

#---------------------------------------------------------------------------

class WPTaskDetailsResponsibleSelect( WPCategoryDisplayBase ):
    
        
    def _getBody( self, params ):
        url = self._rh.getCurrentURL()
        url.addParam("taskId",params["taskId"])
        searchAction = str(url)
        p = wcomponents.WCategoryComplexSelection(self._target,searchAction)
        return p.getHTML(params)

#---------------------------------------------------------------------------

class WPTaskDetailsResponsibleNew( WPCategoryDisplayBase ):
    
    def __init__( self, rh, target, params ):
        WPCategoryDisplayBase.__init__( self, rh, target )
        self._params = params
    
    def _getBody( self, params ):
        p = wcomponents.WNewPerson()
        
        params.update(self._params)
        if params.get("formTitle",None) is None :
            params["formTitle"] = _("Define new responsible")
        if params.get("titleValue",None) is None :
            params["titleValue"] = ""
        if params.get("surNameValue",None) is None :
            params["surNameValue"] = ""
        if params.get("nameValue",None) is None :
            params["nameValue"] = ""
        if params.get("emailValue",None) is None :
            params["emailValue"] = ""
        if params.get("addressValue",None) is None :
            params["addressValue"] = ""
        if params.get("affiliationValue",None) is None :
            params["affiliationValue"] = ""
        if params.get("phoneValue",None) is None :
            params["phoneValue"] = ""
        if params.get("faxValue",None) is None :
            params["faxValue"] = ""
        
        params["disabledSubmission"] = False
        params["submissionValue"] = _(""" <input type="checkbox" name="submissionControl"> _("Give submission rights to the presenter").""")
        params["disabledNotice"] = False
        params["noticeValue"] = _("""<i><font color="black"><b>_("Note"): </b></font>_("If this person does not already have
         an Indico account, he or she will be sent an email asking to create an account. After the account creation the 
         user will automatically be given submission rights.")</i>""")
        
        formAction = urlHandlers.UHTaskDetailsPersonAdd.getURL(self._target)
        formAction.addParam("orgin","new")
        formAction.addParam("typeName","responsible")
        formAction.addParam("taskId",params["taskId"])
        params["formAction"] = formAction
        
        return p.getHTML(params)



#------------------------------------------------------------------------------

class WTaskComment(wcomponents.WTemplated):
        
    def __init__( self, target):
        self._target = target

    def getHTML( self, params ):        
        return wcomponents.WTemplated.getHTML( self, params )
    
    def getVars( self ):        
        vars = wcomponents.WTemplated.getVars( self )
        
        vars["name"] = self._target.getName()
        vars["img"] = Config.getInstance().getSystemIconURL( "category" )
        vars["description"] = "&nbsp;"  
        vars["conferenceList"] = urlHandlers.UHCategoryDisplay.getURL(self._target)  
        vars["taskList"] = urlHandlers.UHTaskList.getURL(self._target)  
        vars["taskCommentTitle"] = vars.get("taskCommentTitle", _("Task Comment Details"))        
        vars["taskDetailsAction"] = vars.get("taskDetailsAction","")        
            
        mgrs=[]
        from MaKaC.user import Avatar
        for mgr in self._target.getManagerList():
            if isinstance(mgr, Avatar):
               mgrs.append(mgr.getAbrName())
        vars["managers"]=""
        if mgrs != []:
            vars["managers"]= _("""(<b> _("Managers")</b>: %s)""")%"; ".join(mgrs)
        
        taskObject = self._target.getTask(vars["taskId"])
        vars["taskTitle"] = taskObject.getTitle()
        vars["taskStatus"] = taskObject.getCurrentStatus().getStatusName()
        vars["taskDescription"] = taskObject.getDescription()
        vars["createdBy"] = taskObject.getCreatedBy().getFullName()
        vars["creatorId"] = taskObject.getCreatedBy().getId()
                
        responsibleList = []
        for r in taskObject.getResponsibleList() :
            responsibleList.append(r.getFullName())
        vars["responsibleList"] = ", ".join(responsibleList)
        
        commentedBy = ""
        commentText = ""
        if vars.get("commentKey",None) is not None :
            commentBy = taskObject.getCommentHistry()[vars["commentKey"]].getCommentAuthor().getFullName()
            commentText = taskObject.getCommentHistry()[vars["commentKey"]].getCommentText()
        vars["commentedBy"] = vars.get("commentedBy",commentedBy)
        vars["commentText"] = vars.get("commentText",commentText)
                
        return vars
            
            
class WPTaskCommentNew( WPCategoryDisplayBase ):
    
    def __init__( self, rh, target, params ):
        WPCategoryDisplayBase.__init__( self, rh, target )
        self._params = params
    
    def _getBody( self, params ):
        
        wc = WTaskComment( self._target )
        pars = { "categDisplayURLGen": urlHandlers.UHCategoryDisplay.getURL, \
                "confDisplayURLGen": urlHandlers.UHConferenceDisplay.getURL }
        params.update(pars)
        params.update(self._params)
        params["taskCommentTitle"] = _("Task Details")
        url = urlHandlers.UHTaskCommentNewAction.getURL(self._target)
        params["taskCommentAction"] = url
        
        params["commentedBy"] = params.get("commentedBy","")
        commentText = """
        <textarea name="commentText" cols="65" rows="10"></textarea>
        """
        params["commentText"] = commentText
        
        return wc.getHTML( params )    
    
    
    def _getNavigationDrawer(self):
        pars = {"target": self._target, "isModif": False}
        return wcomponents.WNavigationDrawer( pars )

