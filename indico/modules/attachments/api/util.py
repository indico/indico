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

from indico.modules.attachments.util import get_attached_folders
from indico.modules.attachments.models.attachments import AttachmentType
from indico.modules.attachments.models.folders import AttachmentFolder
from MaKaC.common.contextManager import ContextManager


def build_material_legacy_api_data(linked_object):
    # Skipping root folder and files in legacy API
    folder_query = (AttachmentFolder
                    .find(linked_object=linked_object, is_deleted=False, is_default=False)
                    .options(joinedload(AttachmentFolder.legacy_mapping), joinedload(AttachmentFolder.attachments)))
    return filter(None, (_build_folder_legacy_api_data(folder) for folder in folder_query))


def _build_folder_legacy_api_data(folder):
    avatar = ContextManager.get("currentAW").getUser()
    user = avatar.user if avatar else None
    if not folder.can_access(user):
        return None

    resources = [_build_attachment_legacy_api_data(attachment)
                 for attachment in folder.attachments
                 if attachment.can_access(user)]
    if not resources:  # Skipping empty folders for legacy API
        return None

    type_ = (folder.legacy_mapping.material_id.title()
             if folder.legacy_mapping is not None and not folder.legacy_mapping.material_id.isdigit()
             else 'Material')
    return {
        '_type': type_,
        '_fossil': 'materialMetadata',
        'title': folder.title,
        'id': str(folder.id),
        'resources': resources
    }


def _build_attachment_legacy_api_data(attachment):
    data = {'name': attachment.title}

    if attachment.type == AttachmentType.file:
        data['_type'] = 'LocalFile'
        data['_fossil'] = 'localFileMetadata'
        data['id'] = str(attachment.id)
        data['fileName'] = attachment.file.filename
        data['url'] = attachment.absolute_download_url

    elif attachment.type == AttachmentType.link:
        data['_type'] = 'Link'
        data['_fossil'] = 'linkMetadata'
        data['url'] = attachment.link_url

    return data


def build_folders_api_data(linked_object):
    if not linked_object:
        return []
    folders = get_attached_folders(linked_object)
    if not folders:
        return []
    return filter(None, (_build_folder_api_data(folder) for folder in folders))


def _build_folder_api_data(folder):
    avatar = ContextManager.get("currentAW").getUser()
    user = avatar.user if avatar else None
    if not folder.can_view(user):
        return None

    return {
        'id': folder.id,
        'title': folder.title,
        'description': folder.description,
        'attachments': [_build_attachment_api_data(attachment)
                        for attachment in folder.attachments
                        if attachment.can_access(user)],
        'default_folder': folder.is_default
    }


def _build_attachment_api_data(attachment):
    data = {
        'id': attachment.id,
        'download_url': attachment.absolute_download_url,
        'title': attachment.title,
        'description': attachment.description,
        'modified_dt': attachment.modified_dt.isoformat(),
        'type': attachment.type.name,
    }

    if attachment.type == AttachmentType.file:
        data['filename'] = attachment.file.filename
        data['content_type'] = attachment.file.content_type
        data['size'] = attachment.file.size

    elif attachment.type == AttachmentType.link:
        data['link_url'] = attachment.link_url

    return data
