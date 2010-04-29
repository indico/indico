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
from datetime import timedelta, datetime
from MaKaC.common.timezoneUtils import nowutc

class LogItem(Persistent) :
    
    def __init__(self, user, logInfo, module):
        self._logId = None
        self._logDate = nowutc()
        self._logType = "generalLog"
        """
        user who has performed / authorised the logged action
        """
        self._responsibleUser = user
        
        """
        Indico module, the logged action comes from
        """
        self._module = module
        
        """
        DICTIONARY containing infos that have to be logged
        MUST CONTAIN entry with key : "subject" 
        keys as well as values should be meaningful
        """
        self._logInfo = logInfo
        if self._logInfo.get("subject", None) is None :
            self._logInfo["subject"] = "%s : %s : %s"%(self._logDate, self._module, self._logType)
    
    def getLogId(self):
        return self._logId
        
    def setLogId(self, id):
        if self._logId is not None :
            return False
        self._logId = id
        return True
            
    def getLogDate(self):
        return self._logDate
        
    def getLogType(self):
        return self._logType
        
    def getResponsible(self):
        return self._responsibleUser
        
    def getResponsibleName(self):
        if self._responsibleUser is None :
            return "<system>"
        else :
            return self._responsibleUser.getFullName()
            
    def getModule(self):
        return self._module
        
    def getLogInfo(self):
        return self._logInfo
        
    def getLogSubject(self):
        return self._logInfo["subject"]
        
    
class ActionLogItem(LogItem):    
    
    def __init__(self, user, logInfo, module):
        LogItem.__init__(self, user, logInfo, module)
        self._logType = "actionLog"
        
        
class EmailLogItem(LogItem):    
    
    def __init__(self, user, logInfo, module):
        LogItem.__init__(self, user, logInfo, module)
        self._logType = "emailLog"
        

class LogHandler(Persistent):        
    
    def __init__(self):
        self._logLists = {}
        self._logLists["generalLog"] = {}
        self._logLists["emailLog"] = []
        self._logLists["actionLog"] = []
        self._logIdGenerator = 0

    def _newLogId(self):    
        self._logIdGenerator += 1
        return self._logIdGenerator

    def _lastLogId(self):
        return self._logIdGenerator
        
    def _cmpLogDate(logItem1, logItem2):
        return cmp(logItem2.getLogDate(), logItem1.getLogDate())
    _cmpLogDate = staticmethod(_cmpLogDate)
    
    def _cmpLogModule(logItem1, logItem2):
        return cmp(logItem1.getModule(), logItem2.getModule())
    _cmpLogModule = staticmethod(_cmpLogModule)
    
    def _cmpLogSubject(logItem1, logItem2):
        return cmp(logItem1.getLogSubject(), logItem2.getLogSubject())
    _cmpLogSubject = staticmethod(_cmpLogSubject)
    
    def _cmpLogResponsibleName(logItem1, logItem2):
        return cmp(logItem1.getResponsibleName(), logItem2.getResponsibleName())
    _cmpLogResponsibleName = staticmethod(_cmpLogResponsibleName)
    
    def _cmpLogType(logItem1, logItem2):
        return cmp(logItem1.getLogType(), logItem2.getLogType())
    _cmpLogType= staticmethod(_cmpLogType)
    
    def getEmailLogList(self, order="date"):
        list = self._logLists["emailLog"]
        if order == "date" :
            list.sort(LogHandler._cmpLogDate)
            return list
        if order == "subject" :
            list.sort(LogHandler._cmpLogSubject)
            return list
        if order == "responsible" :
            list.sort(LogHandler._cmpLogResponsibleName)
            return list
        if order == "module" :
            list.sort(LogHandler._cmpLogModule)
            return list
        if order == "type" :
            list.sort(LogHandler._cmpLogType)
            return list
        return self._logLists["emailLog"]
            
    def getActionLogList(self, order="date"):
        list = self._logLists["actionLog"]
        if order == "date" :
            list.sort(LogHandler._cmpLogDate)
            return list
        if order == "subject" :
            list.sort(LogHandler._cmpLogSubject)
            return list
        if order == "responsible" :
            list.sort(LogHandler._cmpLogResponsibleName)
            return list
        if order == "module" :
            list.sort(LogHandler._cmpLogModule)
            return list
        if order == "type" :
            list.sort(LogHandler._cmpLogType)
            return list
        return self._logLists["actionLog"]
    
    def getGeneralLogList(self, order="date"):
        list = self._logLists["generalLog"].values()
        if order == "date" :
            list.sort(LogHandler._cmpLogDate)
            return list
        elif order == "subject" :
            list.sort(LogHandler._cmpLogSubject)
            return list
        elif order == "responsible" :
            list.sort(LogHandler._cmpLogResponsibleName)
            return list
        elif order == "module" :
            list.sort(LogHandler._cmpLogModule)
            return list
        if order == "type" :
            list.sort(LogHandler._cmpLogType)
            return list
        return self._logLists["generalLog"].values()
        
    def getCustomLogList(self, key, order="date"):
        
        list = []
        for li in self._logLists["generalLog"].values() :
            if li.getResponsibleName().lower().find(key.lower()) >= 0 :
                list.append(li)
            else :
                for v in li.getLogInfo().values() :
                    value = "%s"%v
                    if value.lower().find(key.lower()) >= 0 :
                        list.append(li)
                        break
        if order == "date" :
            list.sort(LogHandler._cmpLogDate)
        elif order == "subject" :
            list.sort(LogHandler._cmpLogSubject)
            return list
        elif order == "responsible" :
            list.sort(LogHandler._cmpLogResponsibleName)
            return list
        elif order == "module" :
            list.sort(LogHandler._cmpLogModule)
            return list
        if order == "type" :
            list.sort(LogHandler._cmpLogType)
            return list
        return list
        
        
    def getLogItemById(self, logId):
        if logId is None :
            return None
        return self._logLists["generalLog"].get(logId, None)
        
    def addLogItem(self, logItem):
        if logItem is None :
            return False
        logItem.setLogId(self._newLogId())
        self._logLists[logItem.getLogType()].append(logItem)
        self._logLists["generalLog"]["%s"%self._lastLogId()] = logItem
        self.notifyModification()
        return True
        
    def logEmail(self, logInfo, module, user=None):    
        if logInfo is None :
            return False
        logItem = EmailLogItem(user, logInfo, module)
        self.addLogItem(logItem)
        return True
    
    def logAction(self, logInfo, module, user=None):    
        if logInfo is None :
            return False
        logItem = ActionLogItem(user, logInfo, module)
        self.addLogItem(logItem)
        return True
    
    def notifyModification(self):
        self._p_changed=1
        

    
