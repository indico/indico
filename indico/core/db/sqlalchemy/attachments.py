# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from sqlalchemy.ext.declarative import declared_attr

from indico.core.db import db
from indico.modules.attachments.util import get_attached_items, can_manage_attachments
from indico.util.caching import memoize_request


class AttachedItemsMixin(object):
    """Allows for easy retrieval of structured information about
       items attached to the object"""

    #: When set to ``True`` will preload all items that exist for the same event.
    #: Should be set to False when not applicable (no object.event[_new] property).
    PRELOAD_EVENT_ATTACHED_ITEMS = False
    #: The name of the AttachmentFolder column pointing to to the object's ID
    ATTACHMENT_FOLDER_ID_COLUMN = None

    @property
    @memoize_request
    def attached_items(self):
        return get_attached_items(self, include_empty=False, include_hidden=False,
                                  preload_event=self.PRELOAD_EVENT_ATTACHED_ITEMS)

    @declared_attr
    def attachment_count(cls):
        from indico.modules.attachments import AttachmentFolder, Attachment
        query = (db.select([db.func.count(Attachment.id)])
                 .select_from(db.join(Attachment, AttachmentFolder, Attachment.folder_id == AttachmentFolder.id))
                 .where(db.and_(
                     ~AttachmentFolder.is_deleted,
                     ~Attachment.is_deleted,
                     (getattr(AttachmentFolder, cls.ATTACHMENT_FOLDER_ID_COLUMN) == cls.id)
                 ))
                 .correlate_except(AttachmentFolder, Attachment))
        return db.column_property(query, deferred=True)

    def can_manage_attachments(self, user):
        return can_manage_attachments(self, user)
