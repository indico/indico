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


def get_attached_items(linked_object, include_empty=True, include_hidden=True, preload_event=False):
    """
    Return a structured representation of all the attachments linked
    to an object.

    :param linked_object: The object whose attachments are to be returned
    :param include_empty: Whether to return empty folders as well.
    :param include_hidden: Include folders that the user can't see
    :param preload_event: in the process, preload all objects tied to the
                          corresponding event and keep them in cache
    """
    from indico.modules.attachments.models.folders import AttachmentFolder

    folders = AttachmentFolder.get_for_linked_object(linked_object, preload_event=preload_event)

    if not include_hidden:
        folders = [f for f in folders if f.can_view(session.user)]

    if not include_empty:
        folders = [f for f in folders if f.attachments]

    if not folders:
        return {}
    # the default folder is never shown as a folder. instead, its
    # files are shown on the same level as other folders
    files = folders.pop(0).attachments if folders[0].is_default else []
    if not files and not folders:
        return {}
    return {
        'folders': folders,
        'files': files
    }


def can_manage_attachments(obj, user):
    """Checks if a user can manage attachments for the object"""
    from MaKaC.conference import Contribution, Session, SubContribution
    if not user:
        return False
    if isinstance(obj, Session) and obj.canCoordinate(user.as_avatar):
        return True
    if isinstance(obj, Contribution) and obj.canUserSubmit(user.as_avatar):
        return True
    if isinstance(obj, SubContribution):
        return can_manage_attachments(obj.getContribution(), user)
    return obj.canModify(user.as_avatar)
