# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import jsonify, session
from werkzeug.exceptions import Forbidden, NotFound

from indico.modules.attachments.controllers.event_package import AttachmentPackageMixin
from indico.modules.attachments.controllers.management.base import (AddAttachmentFilesMixin, AddAttachmentLinkMixin,
                                                                    CreateFolderMixin, DeleteAttachmentMixin,
                                                                    DeleteFolderMixin, EditAttachmentMixin,
                                                                    EditFolderMixin, ManageAttachmentsMixin)
from indico.modules.attachments.util import can_manage_attachments
from indico.modules.attachments.views import WPEventAttachments, WPPackageEventAttachmentsManagement
from indico.modules.events.controllers.base import RHEventBase
from indico.modules.events.management.controllers import RHManageEventBase
from indico.modules.events.util import check_event_locked, get_object_from_args
from indico.web.flask.templating import get_template_module
from indico.web.rh import RHProtected


class RHEventAttachmentManagementBase(RHEventBase, RHProtected):
    normalize_url_spec = {
        'locators': {
            lambda self: self.object
        }
    }

    def _process_args(self):
        RHEventBase._process_args(self)
        self.object_type, self.base_object, self.object = get_object_from_args()
        if self.object is None:
            raise NotFound

    def _check_access(self):
        RHProtected._check_access(self)
        if not can_manage_attachments(self.object, session.user):
            raise Forbidden
        check_event_locked(self, self.event)


class RHManageEventAttachments(ManageAttachmentsMixin, RHEventAttachmentManagementBase):
    wp = WPEventAttachments


class RHAttachmentManagementInfoColumn(RHEventAttachmentManagementBase):
    def _process(self):
        tpl = get_template_module('attachments/_management_info_column.html')
        return jsonify(html=tpl.render_attachment_info(self.object))


class RHAddEventAttachmentFiles(AddAttachmentFilesMixin, RHEventAttachmentManagementBase):
    pass


class RHAddEventAttachmentLink(AddAttachmentLinkMixin, RHEventAttachmentManagementBase):
    pass


class RHEditEventAttachment(EditAttachmentMixin, RHEventAttachmentManagementBase):
    def _process_args(self):
        RHEventAttachmentManagementBase._process_args(self)
        EditAttachmentMixin._process_args(self)


class RHCreateEventFolder(CreateFolderMixin, RHEventAttachmentManagementBase):
    pass


class RHEditEventFolder(EditFolderMixin, RHEventAttachmentManagementBase):
    def _process_args(self):
        RHEventAttachmentManagementBase._process_args(self)
        EditFolderMixin._process_args(self)


class RHDeleteEventFolder(DeleteFolderMixin, RHEventAttachmentManagementBase):
    def _process_args(self):
        RHEventAttachmentManagementBase._process_args(self)
        DeleteFolderMixin._process_args(self)


class RHDeleteEventAttachment(DeleteAttachmentMixin, RHEventAttachmentManagementBase):
    def _process_args(self):
        RHEventAttachmentManagementBase._process_args(self)
        DeleteAttachmentMixin._process_args(self)


class RHPackageEventAttachmentsManagement(AttachmentPackageMixin, RHManageEventBase):
    wp = WPPackageEventAttachmentsManagement
    management = True
    ALLOW_LOCKED = True
