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
                                                                    CreateFolderMixin, EditFolderMixin,
                                                                    DeleteFolderMixin, DeleteAttachmentMixin)
from indico.modules.attachments.util import can_manage_attachments
from indico.modules.attachments.controllers.event_package import AttachmentPackageMixin
from indico.modules.attachments.views import (WPContributionAttachments, WPEventAttachments, WPSessionAttachments,
                                              WPSubContributionAttachments, WPPackageEventAttachmentsManagement)
from indico.modules.events.util import get_object_from_args
from MaKaC.webinterface.rh.base import RHProtected
from MaKaC.webinterface.rh.conferenceBase import RHConferenceBase
from MaKaC.webinterface.rh.conferenceModif import RHConferenceModifBase


class RHEventAttachmentManagementBase(RHConferenceBase, RHProtected):
    CSRF_ENABLED = True

    normalize_url_spec = {
        'locators': {
            lambda self: self.object
        }
    }

    def _checkParams(self, params):
        RHConferenceBase._checkParams(self, params)
        self.object_type, self.base_object, self.object = get_object_from_args()
        if self.object is None:
            raise NotFound

    def _checkProtection(self):
        RHProtected._checkProtection(self)
        if not can_manage_attachments(self.object, session.user):
            raise Forbidden


class RHManageEventAttachments(ManageAttachmentsMixin, RHEventAttachmentManagementBase):
    _wp_mapping = {
        'event': WPEventAttachments,
        'session': WPSessionAttachments,
        'contribution': WPContributionAttachments,
        'subcontribution': WPSubContributionAttachments
    }

    @property
    def wp(self):
        return self._wp_mapping[self.object_type]


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


class RHEditEventFolder(EditFolderMixin, RHEventAttachmentManagementBase):
    def _checkParams(self, params):
        RHEventAttachmentManagementBase._checkParams(self, params)
        EditFolderMixin._checkParams(self)


class RHDeleteEventFolder(DeleteFolderMixin, RHEventAttachmentManagementBase):
    def _checkParams(self, params):
        RHEventAttachmentManagementBase._checkParams(self, params)
        DeleteFolderMixin._checkParams(self)


class RHDeleteEventAttachment(DeleteAttachmentMixin, RHEventAttachmentManagementBase):
    def _checkParams(self, params):
        RHEventAttachmentManagementBase._checkParams(self, params)
        DeleteAttachmentMixin._checkParams(self)


class RHPackageEventAttachmentsManagement(AttachmentPackageMixin, RHConferenceModifBase):
    wp = WPPackageEventAttachmentsManagement
    management = True
    CSRF_ENABLED = True
