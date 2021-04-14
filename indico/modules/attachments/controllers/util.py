# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import request
from werkzeug.exceptions import NotFound

from indico.modules.attachments.models.attachments import Attachment, AttachmentType
from indico.modules.attachments.models.folders import AttachmentFolder


class SpecificAttachmentMixin:
    """Mixin for RHs that reference a specific attachment."""

    normalize_url_spec = {
        'args': {
            'folder_id': lambda self: self.attachment.folder_id,
            'filename': lambda self: (self.attachment.file.filename if self.attachment.type == AttachmentType.file
                                      else 'go')
        },
        'locators': {
            lambda self: self.attachment.folder.object
        },
        'preserved_args': {'attachment_id'}
    }

    def _process_args(self):
        self.attachment = Attachment.query.filter_by(id=request.view_args['attachment_id'], is_deleted=False).one()
        if self.attachment.folder.is_deleted:
            raise NotFound


class SpecificFolderMixin:
    """Mixin for RHs that reference a specific folder."""

    normalize_url_spec = {
        'locators': {
            lambda self: self.folder.object
        },
        'preserved_args': {'folder_id'}
    }

    def _process_args(self):
        self.folder = AttachmentFolder.query.filter_by(id=request.view_args['folder_id'], is_deleted=False).one()
