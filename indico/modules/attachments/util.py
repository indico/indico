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

from sqlalchemy.orm import joinedload

from indico.core.db import db
from indico.modules.attachments.models.folders import AttachmentFolder


def get_attached_items(linked_object, include_deleted=False):
    """
    Return a structured representation of all the attachments linked
    to an object.

    :param linked_object: The object whose attachments are to be returned
    :param include_deleted: Whether to return deleted attachments or
                            folders as well
    """
    kwargs = {}
    if not include_deleted:
        kwargs['is_deleted'] = False

    folders = (AttachmentFolder
               .find(linked_object=linked_object, **kwargs)
               .order_by(AttachmentFolder.is_default.desc(), db.func.lower(AttachmentFolder.title))
               .options(joinedload(AttachmentFolder.attachments))
               .all())
    if not folders:
        return {}
    # the default folder is never shown as a folder. instead, its
    # files are shown on the same level as other folders
    files = folders.pop(0).attachments if folders[0].is_default else []
    return {
        'folders': folders,
        'files': files
    }
