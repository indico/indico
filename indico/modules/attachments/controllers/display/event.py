# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

from flask import redirect, request, session
from werkzeug.exceptions import Forbidden

from indico.legacy.webinterface.rh.conferenceBase import RHConferenceBase
from indico.legacy.webinterface.rh.conferenceDisplay import RHConferenceBaseDisplay
from indico.modules.attachments.controllers.display.base import DownloadAttachmentMixin
from indico.modules.attachments.controllers.event_package import AttachmentPackageMixin
from indico.modules.attachments.controllers.util import SpecificFolderMixin
from indico.modules.attachments.views import (WPEventFolderDisplay, WPPackageEventAttachmentsDisplay,
                                              WPPackageEventAttachmentsDisplayConference)
from indico.modules.events.models.events import EventType


class RHDownloadEventAttachment(DownloadAttachmentMixin, RHConferenceBase):
    def _checkParams(self, params):
        RHConferenceBase._checkParams(self, params)
        DownloadAttachmentMixin._checkParams(self)


class RHListEventAttachmentFolder(SpecificFolderMixin, RHConferenceBaseDisplay):
    def _checkParams(self, params):
        RHConferenceBaseDisplay._checkParams(self, params)
        SpecificFolderMixin._checkParams(self)

    def _checkProtection(self):
        RHConferenceBaseDisplay._checkProtection(self)
        if not self.folder.can_access(session.user):
            raise Forbidden

    def _process(self):
        if request.args.get('redirect_if_single') == '1' and len(self.folder.attachments) == 1:
            return redirect(self.folder.attachments[0].download_url)

        return WPEventFolderDisplay.render_template('folder.html', self._conf, folder=self.folder, event=self.event_new)


class RHPackageEventAttachmentsDisplay(AttachmentPackageMixin, RHConferenceBaseDisplay):
    @property
    def wp(self):
        if self.event_new.type_ == EventType.conference:
            return WPPackageEventAttachmentsDisplayConference
        else:
            return WPPackageEventAttachmentsDisplay
