# -*- coding: utf-8 -*-
#
#
# This file is part of Indico.
# Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico;if not, see <http://www.gnu.org/licenses/>.

import os
from flask import current_app
from indico.core.db import DBMgr
from indico.core.config import Config
from MaKaC.common.mail import GenericMailer
from indico.modules import ModuleHolder
from indico.modules.scheduler.tasks import OneShotTask
from MaKaC.webinterface.mail import GenericNotification
from MaKaC.webinterface.urlHandlers import UHOfflineEventAccess
from indico.core.logger import Logger
from MaKaC.common.timezoneUtils import nowutc
from MaKaC.webinterface.rh.conferenceBase import RHCustomizable
from indico.util.contextManager import ContextManager
from MaKaC.common.offlineWebsiteCreator import OfflineEvent
from indico.util.i18n import set_session_lang
from MaKaC.accessControl import AccessWrapper
from indico.util import fossilize


class OfflineEventGeneratorTask(OneShotTask):

    def __init__(self, task):
        super(OfflineEventGeneratorTask, self).__init__(task.requestTime)
        self._task = task

    def run(self):
        with current_app.test_request_context():
            self._run()

    def _run(self):
        Logger.get('OfflineEventGeneratorTask').info("Started generation of the offline website for task: %s" %
                                                     self._task.id)
        set_session_lang(self._task.avatar.getLang())
        self._rh = RHCustomizable()
        self._aw = self._rh._aw = AccessWrapper()
        self._rh._conf = self._rh._target = self._task.conference

        ContextManager.set('currentRH', self._rh)
        ContextManager.set('offlineMode', True)

        # Get event type
        wf = self._rh.getWebFactory()
        if wf:
            eventType = wf.getId()
        else:
            eventType = "conference"

        try:
            websiteZipFile = OfflineEvent(self._rh, self._rh._conf, eventType).create()
        except Exception, e:
            Logger.get('OfflineEventGeneratorTask').exception("Generation of the offline website for task %s failed \
                with message error: %s" % (self._task.id, e))
            self._task.status = "Failed"
            return

        self._task.creationTime = nowutc()
        if not websiteZipFile:
            Logger.get('OfflineEventGeneratorTask').info("Generation of the offline website for task %s failed" %
                                                         self._task.id)
            self._task.status = "Failed"
            return
        self._task.status = "Generated"
        self._task.file = websiteZipFile

        Logger.get('OfflineEventGeneratorTask').info("Finished generation of the offline website for task %s" %
                                                     self._task.id)
        ContextManager.set('offlineMode', False)
        notification = OfflineEventGeneratedNotification(self._task)
        GenericMailer.sendAndLog(notification, self._task.conference, "OfflineEventGenerator")


class OfflineEventGeneratedNotification(GenericNotification):

    def __init__(self, task):
        GenericNotification.__init__(self)
        self.setFromAddr("Indico <%s>" % Config.getInstance().getNoReplyEmail())
        self.setToList([task.avatar.getEmail()])
        self.setSubject("""
The offline version of the event "%s" is ready to be downloaded
""" % (task.conference.getTitle()))
        self.setBody("""
Dear %s,

The offline version for the event "%s" was successfully generated and it is ready to be downloaded.

Download link: %s

Best Regards,
--
Indico""" % (task.avatar.getStraightFullName(), task.conference.getTitle(), task.getDownloadLink()))
