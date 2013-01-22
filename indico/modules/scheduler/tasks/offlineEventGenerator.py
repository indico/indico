# -*- coding: utf-8 -*-
#
#
# This file is part of Indico.
# Copyright (C) 2002 - 2012 European Organization for Nuclear Research (CERN).
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

from MaKaC.common import DBMgr
from MaKaC.common import Config
from MaKaC.common.mail import GenericMailer
from indico.modules import ModuleHolder
from indico.modules.scheduler.tasks import OneShotTask
from MaKaC.webinterface.mail import GenericNotification
from MaKaC.webinterface.urlHandlers import UHOfflineEventAccess
from MaKaC.webinterface.pages.static import WPTPLStaticConferenceDisplay, WPStaticConferenceDisplay
from MaKaC.common.logger import Logger
from MaKaC.common.timezoneUtils import nowutc
from MaKaC.webinterface.rh.conferenceBase import RHCustomizable
from indico.util.contextManager import ContextManager
import MaKaC.common.info as info
from MaKaC.common.offlineWebsiteCreator import OfflineEvent
import MaKaC.webinterface.displayMgr as displayMgr
from indico.util.i18n import setLocale
from MaKaC.accessControl import AccessWrapper


class FakeRequest():

    def __init__(self):
        self.headers_in = {}
        self.unparsed_uri = ""
        self.remote_ip = "127.0.0.1"

    def get_remote_ip(self):
        return "127.0.0.1"

    def is_https(self):
        return False

    def construct_url(self, uri):
        return ""

class OfflineEventGeneratorTask(OneShotTask):

    def __init__(self, task):
        super(OfflineEventGeneratorTask, self).__init__(task.requestTime)
        self._task = task

    def run(self):
        Logger.get('OfflineEventGeneratorTask').info("Stared generation of ZIP file for task: %s" % self._task.id)

        websiteZipFile = None

        setLocale(self._task.avatar.getLang())
        self._rh = RHCustomizable(FakeRequest())
        self._aw = self._rh._aw = AccessWrapper()
        self._rh._conf = self._rh._target = self._task.conference
        
        ContextManager.set('currentRH', self._rh)
        ContextManager.set('offlineMode', True)
        
        # Get event type
        displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._rh._target).setSearchEnabled(False)
        wf = self._rh.getWebFactory()
        if wf:
            eventType = wf.getId()
        else:
            eventType = "conference"
        if eventType == "conference":
            p = WPStaticConferenceDisplay(self._rh, self._rh._target)
            html = p.display()
        else:
            # get default/selected view
            styleMgr = info.HelperMaKaCInfo.getMaKaCInfoInstance().getStyleManager()
            view = displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._rh._target).getDefaultStyle()
            # if no default view was attributed, then get the configuration default
            if view == "" or not styleMgr.existsStyle(view) or view in styleMgr.getXSLStyles():
                view = styleMgr.getDefaultStyleForEventType(eventType)
            p = WPTPLStaticConferenceDisplay(self._rh, self._rh._target, view, eventType, self._rh._reqParams)
            html = p.display(**self._rh._getRequestParams())

        websiteZipFile = OfflineEvent(self._rh, self._rh._conf, eventType, html).create()
        displayMgr.ConfDisplayMgrRegistery().getDisplayMgr(self._rh._target).setSearchEnabled(True)

        self._task.creationTime = nowutc()
        if not websiteZipFile:
            Logger.get('OfflineEventGeneratorTask').info("generation ZIP file for task %s failed" % self._task.id)
            self._task.status = "Failed"
            return
        self._task.status = "Generated"
        self._task.file = websiteZipFile

        Logger.get('OfflineEventGeneratorTask').info("Finished generation ZIP file for task %s" % self._task.id)
        notification = OfflineEventGeneratedNotification(self._task)
        GenericMailer.sendAndLog(notification, self._task.conference, "OfflineEventGenerator")


class OfflineEventGeneratedNotification(GenericNotification):

    def __init__(self, task):
        GenericNotification.__init__(self)
        self.setFromAddr("Indico <%s>" % Config.getInstance().getNoReplyEmail())
        self.setToList([task.avatar.getEmail()])
        self.setSubject("""
Offline version of the event "%s" is ready to download
""" % (task.conference.getTitle()))
        self.setBody("""
Dear %s,

Offline version for the event "%s" was successfully generated and it is ready to download.

Download link: %s

Best Regards,

--
Indico""" % (task.avatar.getStraightFullName(), task.conference.getTitle(), task.getDownloadLink()))
