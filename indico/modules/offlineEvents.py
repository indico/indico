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

import os
from persistent import Persistent
from MaKaC.common.Counter import Counter
from indico.modules import ModuleHolder, Module
from indico.util.i18n import L_, _
from MaKaC.common.timezoneUtils import nowutc
from BTrees.OOBTree import OOBTree
from MaKaC.webinterface.urlHandlers import UHOfflineEventAccess


class OfflineEventsModule(Module):
    """
    This module holds all the information needed to keep the creation process of the offline version of the events.
    That means all the news items and other related information.
    """

    id = "offlineEvents"
    _offlineEventTypes = {"Queued": L_("Queued"), "Generated": L_("Generated"), "Failed": L_("Failed"),
                          "Expired": L_("Expired")}

    def __init__(self):
        self._idxConf = OOBTree()
        self._offlineEventCounter = Counter()

    def getOfflineEventIndex(self):
        return self._idxConf

    def getOfflineEventByConfId(self, confId):
        return self._idxConf.get(confId, [])

    def getOfflineEventByFileId(self, confId, fileId):
        offline_request_list = self._idxConf.get(confId, [])
        for req in offline_request_list:
            if req.id == fileId:
                return req
        return None

    def addOfflineEvent(self, offlineEvent):
        confId = offlineEvent.conference.getId()
        if not self._idxConf.has_key(confId):
            lst = []
            self._idxConf[confId] = lst
        else:
            lst = self._idxConf[confId]
        offlineEvent.id = self._offlineEventCounter.newCount()
        lst.append(offlineEvent)
        self._idxConf[confId] = lst

    def removeOfflineEvent(self, offlineEvent, del_file=False):
        if offlineEvent:
            confId = offlineEvent.conference.getId()
            lst = self._idxConf.get(confId,[])
            if offlineEvent in lst:
                lst.remove(offlineEvent)
            self._idxConf[confId] = lst
            if del_file:
                self.removeOfflineFile(offlineEvent)
        else:
            raise Exception(_("OfflineEvent does not exist"))

    def removeOfflineFile(self, offlineEvent):
        filepath = offlineEvent.file.getFilePath()
        if os.path.isfile(filepath):
            os.remove(filepath)
        offlineEvent.status = "Expired"

    @classmethod
    def getOfflineEventTypes(self):
        return OfflineEventsModule._offlineEventTypes

class OfflineEventItem(Persistent):

    def __init__(self, conference, avatar, status):
        self.id = None
        self.conference = conference
        self.avatar = avatar
        self.requestTime = nowutc()
        self.creationTime = None
        self.status = status
        self.file = None

    def getOfflineEventStatusLabel(self):
        return OfflineEventsModule.getOfflineEventTypes()[self.status]

    def getDownloadLink(self):
        if self.file:
            link = UHOfflineEventAccess.getURL()
            link.addParam('fileId', self.id)
            link.addParam('confId', self.conference.getId())
            return link
