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

from indico.core.db import db
from indico.core.db.sqlalchemy.util.models import get_simple_column_attrs
from indico.modules.attachments.models.attachments import Attachment, AttachmentFile, AttachmentType
from indico.modules.attachments.models.folders import AttachmentFolder
from indico.util.i18n import _
from MaKaC.conference import EventCloner


class AttachmentCloner(EventCloner):
    def find_attachments(self):
        return Attachment.find(~AttachmentFolder.is_deleted, ~Attachment.is_deleted,
                               AttachmentFolder.event_id == int(self.event.id), _join=AttachmentFolder)

    def find_folders(self):
        return self.event.as_event.attachment_folders.filter_by(is_deleted=False)

    def get_options(self):
        enabled = bool(self.find_attachments().count())
        return {'attachments': (_("Materials"), enabled, False)}

    def clone(self, new_event, options):
        if 'attachments' not in options:
            return
        folder_mapping = {}
        attrs = get_simple_column_attrs(AttachmentFolder)
        for old_folder in self.find_folders():
            new_folder = AttachmentFolder(event_id=new_event.id, **{attr: getattr(old_folder, attr) for attr in attrs})
            if new_folder.linked_object is None:
                continue
            new_folder.acl = old_folder.acl
            db.session.add(new_folder)
            folder_mapping[old_folder] = new_folder

        attrs = get_simple_column_attrs(Attachment) - {'modified_dt'}
        for old_attachment in self.find_attachments():
            folder = folder_mapping.get(old_attachment.folder)
            if not folder:
                continue
            new_attachment = Attachment(folder=folder, user_id=old_attachment.user_id, acl=old_attachment.acl,
                                        **{attr: getattr(old_attachment, attr) for attr in attrs})
            if new_attachment.type == AttachmentType.file:
                old_file = old_attachment.file
                new_attachment.file = AttachmentFile(
                    attachment=new_attachment,
                    user_id=old_file.user_id,
                    filename=old_file.filename,
                    content_type=old_file.content_type
                )
                with old_file.open() as fd:
                    new_attachment.file.save(fd)
            db.session.add(new_attachment)

        db.session.flush()
