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

from flask import request
from werkzeug.exceptions import NotFound

from indico.modules.attachments.models.attachments import Attachment


class SpecificAttachmentMixin:
    """Mixin for RHs that reference a specific attachment"""

    normalize_url_spec = {
        'folder_id': lambda self: self.attachment.folder_id,
        None: lambda self: self.attachment.folder.linked_object
    }

    def _checkParams(self):
        self.attachment = Attachment.find_one(id=request.view_args['attachment_id'], is_deleted=False)
        if self.attachment.folder.is_deleted:
            raise NotFound
