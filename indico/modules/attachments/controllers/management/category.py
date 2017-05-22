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

from flask import session
from werkzeug.exceptions import Forbidden

from indico.modules.attachments.controllers.management.base import (AddAttachmentFilesMixin, AddAttachmentLinkMixin,
                                                                    CreateFolderMixin, DeleteAttachmentMixin,
                                                                    DeleteFolderMixin, EditAttachmentMixin,
                                                                    EditFolderMixin, ManageAttachmentsMixin)
from indico.modules.attachments.util import can_manage_attachments
from indico.modules.categories.controllers.base import RHManageCategoryBase
from indico.modules.categories.views import WPCategoryManagement


class RHCategoryAttachmentManagementBase(RHManageCategoryBase):
    def _checkParams(self, params):
        RHManageCategoryBase._checkParams(self)
        self.object_type = 'category'
        self.object = self.base_object = self.category

    def _checkProtection(self):
        RHManageCategoryBase._checkProtection(self)
        # This is already covered by CategModifBase, but if we ever add more
        # checks to can_manage_attachments we are on the safe side...
        if not can_manage_attachments(self.object, session.user):
            raise Forbidden


class RHManageCategoryAttachments(ManageAttachmentsMixin, RHCategoryAttachmentManagementBase):
    wp = WPCategoryManagement


class RHAddCategoryAttachmentFiles(AddAttachmentFilesMixin, RHCategoryAttachmentManagementBase):
    pass


class RHAddCategoryAttachmentLink(AddAttachmentLinkMixin, RHCategoryAttachmentManagementBase):
    pass


class RHEditCategoryAttachment(EditAttachmentMixin, RHCategoryAttachmentManagementBase):
    def _checkParams(self, params):
        RHCategoryAttachmentManagementBase._checkParams(self, params)
        EditAttachmentMixin._checkParams(self)


class RHCreateCategoryFolder(CreateFolderMixin, RHCategoryAttachmentManagementBase):
    pass


class RHEditCategoryFolder(EditFolderMixin, RHCategoryAttachmentManagementBase):
    def _checkParams(self, params):
        RHCategoryAttachmentManagementBase._checkParams(self, params)
        EditFolderMixin._checkParams(self)


class RHDeleteCategoryFolder(DeleteFolderMixin, RHCategoryAttachmentManagementBase):
    def _checkParams(self, params):
        RHCategoryAttachmentManagementBase._checkParams(self, params)
        DeleteFolderMixin._checkParams(self)


class RHDeleteCategoryAttachment(DeleteAttachmentMixin, RHCategoryAttachmentManagementBase):
    def _checkParams(self, params):
        RHCategoryAttachmentManagementBase._checkParams(self, params)
        DeleteAttachmentMixin._checkParams(self)
