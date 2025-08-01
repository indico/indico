# This file is part of Indico.
# Copyright (C) 2002 - 2025 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from flask import session

from indico.core.db import db
from indico.util.signals import make_interceptable


def get_attached_folders(linked_object, include_empty=True, include_hidden=True, preload_event=False):
    """Return a list of all the folders linked to an object.

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

    return folders


@make_interceptable
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
    folders = get_attached_folders(linked_object, include_empty=include_empty,
                                   include_hidden=include_hidden, preload_event=preload_event)
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


def can_manage_attachments(obj, user, allow_admin=True):
    """Check if a user can manage attachments for the object."""
    from indico.modules.attachments.settings import attachments_settings
    if not user:
        return False
    if obj.can_manage(user, allow_admin=allow_admin):
        return True
    event = getattr(obj, 'event', None)
    if event and attachments_settings.get(event, 'managers_only'):
        return False
    if isinstance(obj, db.m.Event) and obj.can_manage(user, 'submit', allow_admin=allow_admin):
        return True
    if isinstance(obj, db.m.Contribution) and obj.can_manage(user, 'submit', allow_admin=allow_admin):
        return True
    if isinstance(obj, db.m.SubContribution):
        subcontrib_speakers_can_submit = obj.contribution.event.subcontrib_speakers_can_submit
        if subcontrib_speakers_can_submit and any(speaker.person.user == user for speaker in obj.speakers):
            return True
        return can_manage_attachments(obj.contribution, user, allow_admin=allow_admin)
    return False


def can_generate_attachment_package(event, user):
    """Check if the user can generate a material package."""
    from indico.modules.attachments.settings import AttachmentPackageAccess, attachments_settings
    mode = attachments_settings.get(event, 'generate_package')
    match mode:
        case AttachmentPackageAccess.everyone:
            return True
        case AttachmentPackageAccess.logged_in:
            return user is not None
        case AttachmentPackageAccess.managers:
            return event.can_manage(user)


def get_default_folder_names():
    return [
        'Agenda',
        'Document',
        'Drawings',
        'List of Actions',
        'Minutes',
        'Notes',
        'Paper',
        'Pictures',
        'Poster',
        'Proceedings',
        'Recording',
        'Slides',
        'Summary',
        'Text',
        'Video',
        'Webcast',
    ]


def get_event(linked_object):
    from indico.modules.categories import Category
    if isinstance(linked_object, Category):
        return None
    else:
        return linked_object.event
