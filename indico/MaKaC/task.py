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

from persistent import Persistent
from datetime import datetime,timedelta
from MaKaC.i18n import _
from pytz import timezone
import MaKaC.common.timezoneUtils as timezoneUtils 

statusList = ["just created","work in progress","finalized","for review","closed"]

# ///// Watch out! This is the status list used by the extraction script and that will be added to dictionaries. Don't forget to change it if you change the real statuslist \\\\\
#Status_list_to_be_translated : [ _("just created"), _("work in progress"), _("finalized"), _("for review"), _("closed")]

class Task(Persistent):
    
    def __init__(self, category, id, user):
        self._category = category
        self._id = id
        self._title = ""
        self._description = ""
        self._creationDate = timezoneUtils.nowutc()
        # XXX why use a dict when an array seems sufficient?
        self._statusHistory = {}
        ts = TaskStatus("just created",user)
        self._statusHistory["%s"%ts.getSettingDate()] = ts
        self._responsibleList = []
        # key => creation date
        # value => task comment
        self._commentHistory = {}
        
        
    def getCategory(self):
        return self._category
        
    def getId(self):
        return self._id
        
    def getTitle(self):
        return self._title
        
    def setTitle(self, title):
        self._title = title
        
    def getDescription(self):
        return self._description
        
    def setDescription(self, description):
        self._description = description
        
    def getCreationDate(self):
        return self._creationDate
    
    def getCreatedBy(self):
        dates = self._statusHistory.keys()[:]
        dates.sort()
        status = self._statusHistory[dates[0]]
        return status.getUserWhoSet()
    
    def getCurrentStatus(self):
        dates = self._statusHistory.keys()[:]
        dates.sort()
        return self._statusHistory[dates[len(dates)-1]]
    
    def getStatusHistory(self):
        return self._statusHistory
        
    def getStatusHistoryEntries(self):
        entries = self._statusHistory.values()
        entries.sort(sortStatusByDate)
        return entries
        
    def isChangeAllowed(self, taskStatus):
        lastStatusIndex = statusList.index( self.getCurrentStatus().getStatusName())
        newStatusIndex = statusList.index(taskStatus.getStatusName())
        if (lastStatusIndex >= newStatusIndex) :
            return False
        return True
        
    def changeStatus(self, status):
        if status is None :
            return False
        if not self.isChangeAllowed(status) :
            return False
        self._statusHistory["%s"%status.getSettingDate()] = status
        self.notifyModification()
        return True
        
    def getResponsibleList(self):
        return self._responsibleList
        
    def addResponsible(self, user):
        if user is None :
            return False
        if user in self._responsibleList :
            return False
        self._responsibleList.append(user)        
        self.notifyModification()
        
    def removeResponsible(self, responsible):
        self._responsibleList.remove(responsible)
        self.notifyModification()
        
    def getCommentHistory(self):
        return self._commentHistory
        
    def getCommentHistoryElements(self):
        return self._commentHistory.values()
        
    def getCommentHistorySize(self):
        return len(self._commentHistory.values())
        
    def addComment(self, user, commentText):
        if user is None :            
            return False
        if commentText is None :        
            return False
        tc = TaskComment(user.getFullName(), commentText)
        self._commentHistory["%s"%tc.getCreationDate()] = tc
        self.notifyModification()
        return True

    def getLocator(self):
        loc=self.getCategory().getLocator()
        loc["taskId"]=self.getId()
        return loc
    
    def notifyModification( self ):
        """Method called to notify the current category has been modified.
        """
        self._p_changed=1

    def cmpTaskTitle(task1, task2):
        return cmp(task1.getTitle(), task2.getTitle())
    cmpTaskTitle = staticmethod( cmpTaskTitle )
    
    def cmpTaskId(task1, task2):
        return cmp(task1.getId(), task2.getId())
    cmpTaskId = staticmethod( cmpTaskId )
    
    def cmpTaskCreatedBy(task1, task2):
        return cmp(task1.getCreatedBy(), task2.getCreatedBy())
    cmpTaskCreatedBy = staticmethod( cmpTaskCreatedBy )
    
    def cmpTaskCreationDate(task1, task2):
        return cmp(task1.getCreationDate(), task2.getCreationDate())
    cmpTaskCreationDate = staticmethod( cmpTaskCreationDate )
    
    def cmpTaskCurrentStatus(task1, task2):
        return cmp(task1.getCurrentStatus(), task2.getCurrentStatus())
    cmpTaskCurrentStatus = staticmethod( cmpTaskCurrentStatus )
    
    
              
#------------------------------------------------------------------------------        
        
class TaskStatus(Persistent):
    
    def __init__(self, statusName, user):
        self._userWhoSet = user
        self._statusName = statusName
        self._settingDate = timezoneUtils.nowutc()
        
    def getUserWhoSet(self):
        return self._userWhoSet
        
    def getStatusName(self):
        return self._statusName
        
    def getSettingDate(self):
        return self._settingDate
        
#------------------------------------------------------------------------------        
        
class TaskComment(Persistent):
        
    def __init__(self, user, commentText):
        self._creationDate = timezoneUtils.nowutc()
        self._author = user
        self._commentText = commentText
        
    def getCreationDate(self):
        return self._creationDate
        
    def getCommentAuthor(self):
        return self._author
        
    def getCommentText(self):
        return self._commentText
        
def sortStatusByDate(x,y):
    return cmp(x.getSettingDate(),y.getSettingDate())
