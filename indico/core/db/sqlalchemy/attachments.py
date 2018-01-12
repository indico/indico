# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from sqlalchemy import orm
from sqlalchemy.event import listens_for

from indico.core.db import db
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
        from indico.modules.attachments.util import get_attached_items
        return get_attached_items(self, include_empty=False, include_hidden=False,
                                  preload_event=self.PRELOAD_EVENT_ATTACHED_ITEMS)

    # added below due to import issues
    attachment_count = None

    def can_manage_attachments(self, user):
        from indico.modules.attachments.util import can_manage_attachments
        return can_manage_attachments(self, user)


def _make_attachment_count_column_property(cls):
    from indico.modules.attachments.models.attachments import Attachment
    from indico.modules.attachments.models.folders import AttachmentFolder
    assert cls.attachment_count is None
    query = (db.select([db.func.count(Attachment.id)])
             .select_from(db.join(Attachment, AttachmentFolder, Attachment.folder_id == AttachmentFolder.id))
             .where(db.and_(
                 ~AttachmentFolder.is_deleted,
                 ~Attachment.is_deleted,
                 (getattr(AttachmentFolder, cls.ATTACHMENT_FOLDER_ID_COLUMN) == cls.id)
             ))
             .correlate_except(AttachmentFolder, Attachment))
    cls.attachment_count = db.column_property(query, deferred=True)


@listens_for(orm.mapper, 'after_configured', once=True)
def _mappers_configured():
    # We need to create the column property here since we cannot import
    # Attachment/AttachmentFolder while the models are being defined
    for model in db.Model._decl_class_registry.itervalues():
        if hasattr(model, '__table__') and issubclass(model, AttachedItemsMixin):
            _make_attachment_count_column_property(model)
