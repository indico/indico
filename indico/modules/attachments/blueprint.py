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

from indico.modules.attachments.controllers.management.event import (RHManageEventAttachments,
                                                                     RHAddEventAttachmentFiles,
                                                                     RHAddEventAttachmentLink,
                                                                     RHEditEventAttachmentFile,
                                                                     RHCreateEventFolder,
                                                                     RHDeleteEventFolder,
                                                                     RHDeleteEventAttachment)
from indico.web.flask.wrappers import IndicoBlueprint

_bp = IndicoBlueprint('attachments', __name__, template_folder='templates', virtual_template_folder='attachments')

_bp.add_url_rule('/event/<confId>/manage/attachments/', 'event_management', RHManageEventAttachments,
                 defaults={'object_type': 'event'})
_bp.add_url_rule('/event/<confId>/manage/attachments/add/files', 'upload', RHAddEventAttachmentFiles,
                 methods=('GET', 'POST'), defaults={'object_type': 'event'})
_bp.add_url_rule('/event/<confId>/manage/attachments/add/link', 'add_link', RHAddEventAttachmentLink,
                 methods=('GET', 'POST'), defaults={'object_type': 'event'})
_bp.add_url_rule('/event/<confId>/manage/attachments/<int:folder_id>/<int:attachment_id>/', 'modify_attachment',
                 RHEditEventAttachmentFile, methods=('GET', 'POST'), defaults={'object_type': 'event'})
_bp.add_url_rule('/event/<confId>/manage/attachments/create-folder', 'create_folder', RHCreateEventFolder,
                 methods=('GET', 'POST'), defaults={'object_type': 'event'})
_bp.add_url_rule('/event/<confId>/manage/attachments/<int:folder_id>/', 'delete_folder', RHDeleteEventFolder,
                 methods=('DELETE',), defaults={'object_type': 'event'})
_bp.add_url_rule('/event/<confId>/manage/attachments/<int:folder_id>/<int:attachment_id>/', 'delete_attachment',
                 RHDeleteEventAttachment, methods=('DELETE',), defaults={'object_type': 'event'})
