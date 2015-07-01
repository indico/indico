# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from flask import session
from werkzeug.exceptions import NotFound, Forbidden

from indico.modules.attachments.controllers.management.base import (ManageAttachmentsMixin, AddAttachmentFilesMixin,
                                                                    AddAttachmentLinkMixin, EditAttachmentMixin,
                                                                    CreateFolderMixin, DeleteFolderMixin,
                                                                    DeleteAttachmentMixin)
from indico.modules.attachments.views import WPEventAttachments
from indico.modules.events.util import get_object_from_args
from MaKaC.webinterface.rh.base import RHProtected
from MaKaC.webinterface.rh.conferenceBase import RHConferenceBase


class RHEventAttachmentManagementBase(RHConferenceBase, RHProtected):
    def _checkParams(self, params):
        RHConferenceBase._checkParams(self, params)
        self.object_type, self.event, self.object = get_object_from_args()
        if self.object is None:
            raise NotFound
        self.base_object = self.event

    def _checkProtection(self):
        RHProtected._checkProtection(self)
        if not self._doProcess:
            return
        if self.object_type == 'session' and self.object.canCoordinate(session.avatar):
            return
        if self.object_type == 'contribution' and self.object.canUserSubmit(session.avatar):
            return
        if not self.object.canModify(session.avatar):
            raise Forbidden


class RHManageEventAttachments(ManageAttachmentsMixin, RHEventAttachmentManagementBase):
    wp = WPEventAttachments


class RHAddEventAttachmentFiles(AddAttachmentFilesMixin, RHEventAttachmentManagementBase):
    pass


class RHAddEventAttachmentLink(AddAttachmentLinkMixin, RHEventAttachmentManagementBase):
    pass


class RHEditEventAttachment(EditAttachmentMixin, RHEventAttachmentManagementBase):
    def _checkParams(self, params):
        RHEventAttachmentManagementBase._checkParams(self, params)
        EditAttachmentMixin._checkParams(self)


class RHCreateEventFolder(CreateFolderMixin, RHEventAttachmentManagementBase):
    pass


class RHDeleteEventFolder(DeleteFolderMixin, RHEventAttachmentManagementBase):
    pass


class RHDeleteEventAttachment(DeleteAttachmentMixin, RHEventAttachmentManagementBase):
    def _checkParams(self, params):
        RHEventAttachmentManagementBase._checkParams(self, params)
        DeleteAttachmentMixin._checkParams(self)
