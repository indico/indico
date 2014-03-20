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

from persistent import Persistent

from indico.util.contextManager import ContextManager
from indico.util.struct import iterators
from MaKaC.common.timezoneUtils import nowutc

class ModuleNames:

    MATERIAL = "Material"
    PAPER_REVIEWING = "Paper Reviewing"
    PARTICIPANTS = "Participants"
    REGISTRATION = "Registration"
    TIMETABLE = "Timetable"

    def __init__(self):
        pass


class LogItem(Persistent) :

    def __init__(self, user, logInfo, module):
        self._logId = None
        self._logDate = nowutc()
        self._logType = "generalLog"

        # User who has performed / authorised the logged action
        self._responsibleUser = user if user else ContextManager.get("currentUser")

        # Indico module, the logged action comes from
        self._module = module

        # DICTIONARY containing infos that have to be logged
        # MUST CONTAIN entry with key : "subject"
        # keys as well as values should be meaningful
        self._logInfo = logInfo
        if self._logInfo.get("subject", None) is None :
            self._logInfo["subject"] = "%s : %s : %s" % (self._logDate,
                                                         self._module,
                                                         self._logType)

    def getLogId(self):
        return self._logId

    def setLogId(self, log_id):
        if self._logId is not None :
            return False
        self._logId = log_id
        return True

    def getLogDate(self):
        return self._logDate

    def getLogType(self):
        return self._logType

    def getResponsible(self):
        return self._responsibleUser

    def getResponsibleName(self):
        if self._responsibleUser is None :
            return "System"
        else :
            return self._responsibleUser.getStraightAbrName()

    def getModule(self):
        return self._module

    def getLogInfo(self):
        return self._logInfo

    def getLogSubject(self):
        return self._logInfo["subject"]

    def getLogInfoList(self):
        """
        Return a list of pairs with the caption and the pre-processed
        information to be shown.
        """
        info_list = []
        for entry in iterators.SortedDictIterator(self._logInfo):
            if (entry[0] != "subject"):
                caption = entry[0]
                value = entry[1]
                info_list.append((caption, value))
        return info_list


class ActionLogItem(LogItem):

    def __init__(self, user, logInfo, module):
        LogItem.__init__(self, user, logInfo, module)
        self._logType = "actionLog"


class EmailLogItem(LogItem):
    """
    self._logInfo expected keys:
    - body
    - ccList
    - toList
    """
    def __init__(self, user, logInfo, module):
        LogItem.__init__(self, user, logInfo, module)
        self._logType = "emailLog"

    def getLogBody(self):
        return self._logInfo.get("body", "No message")

    def getLogCCList(self):
        return self._logInfo.get("ccList", "No CC receptors")

    def getLogToList(self):
        return self._logInfo.get("toList", "No receptors")

    def getLogContentType(self):
        return self._logInfo.get("contentType", "text/html")

    def getLogInfoList(self):
        """
        Return a list of pairs with the caption and the pre-processed
        information to be shown.
        """
        info_list = []
        info_list.append(("To", ",".join(self.getLogToList())))
        info_list.append(("CC", ",".join(self.getLogCCList())))
        info_list.append(("Body", self.getLogBody()))
        return info_list


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

    @staticmethod
    def _cmpLogDate(logItem1, logItem2):
        return cmp(logItem2.getLogDate(), logItem1.getLogDate())

    @staticmethod
    def _cmpLogModule(logItem1, logItem2):
        return cmp(logItem1.getModule(), logItem2.getModule())

    @staticmethod
    def _cmpLogSubject(logItem1, logItem2):
        return cmp(logItem1.getLogSubject(), logItem2.getLogSubject())

    @staticmethod
    def _cmpLogRecipients(logItem1, logItem2):
        return cmp(logItem1.getLogRecipients(), logItem2.getLogRecipients())

    @staticmethod
    def _cmpLogResponsibleName(logItem1, logItem2):
        return cmp(logItem1.getResponsibleName(), logItem2.getResponsibleName())

    @staticmethod
    def _cmpLogType(logItem1, logItem2):
        return cmp(logItem1.getLogType(), logItem2.getLogType())

    @staticmethod
    def _sortLogList(log_list, order="date"):
        if order == "date" :
            log_list.sort(LogHandler._cmpLogDate)
        elif order == "subject" :
            log_list.sort(LogHandler._cmpLogSubject)
        elif order == "recipients" :
            log_list.sort(LogHandler._cmpLogRecipients)
        elif order == "responsible" :
            log_list.sort(LogHandler._cmpLogResponsibleName)
        elif order == "module" :
            log_list.sort(LogHandler._cmpLogModule)
        elif order == "type" :
            log_list.sort(LogHandler._cmpLogType)
        return log_list

    def getLogList(self, log_type="general", key="", order="date"):
        """
        log_type can be 'email', 'action', 'general' or 'custom'
        """
        if log_type == "email" :
            log_list = self._logLists["emailLog"]
        elif log_type == "action" :
            log_list = self._logLists["actionLog"]
        elif log_type == "custom" :
            log_list = self._getCustomLogList(key)
        else:
            log_list = self._logLists["generalLog"].values()
        return LogHandler._sortLogList(log_list, order)

    def _getCustomLogList(self, key):
        log_list = []
        for li in self._logLists["generalLog"].values() :
            if li.getResponsibleName().lower().find(key.lower()) >= 0 :
                log_list.append(li)
            else :
                for v in li.getLogInfo().values() :
                    value = "%s" % v
                    if value.lower().find(key.lower()) >= 0 :
                        log_list.append(li)
                        break
        return log_list

    def getLogItemById(self, logId):
        if logId is None :
            return None
        return self._logLists["generalLog"].get(logId, None)

    def _addLogItem(self, logItem):
        if logItem is None :
            return False
        logItem.setLogId(self._newLogId())
        self._logLists[logItem.getLogType()].append(logItem)
        self._logLists["generalLog"]["%s" % self._lastLogId()] = logItem
        self.notifyModification()
        return True

    def logEmail(self, logInfo, module, user=None):
        if logInfo is None :
            return False
        logItem = EmailLogItem(user, logInfo, module)
        self._addLogItem(logItem)
        return True

    def logAction(self, logInfo, module, user=None):
        if logInfo is None :
            return False
        logItem = ActionLogItem(user, logInfo, module)
        self._addLogItem(logItem)
        return True

    def notifyModification(self):
        self._p_changed = 1
