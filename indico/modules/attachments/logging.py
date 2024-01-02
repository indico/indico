# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from functools import wraps

from flask import g
from jinja2.filters import do_filesizeformat

from indico.core import signals
from indico.core.db.sqlalchemy.links import LinkType
from indico.modules.attachments.models.attachments import AttachmentType
from indico.modules.logs import EventLogRealm, LogKind
from indico.modules.logs.models.entries import CategoryLogRealm


def connect_log_signals():
    signals.attachments.folder_created.connect(_log_folder_created)
    signals.attachments.folder_deleted.connect(_log_folder_deleted)
    signals.attachments.folder_updated.connect(_log_folder_updated)
    signals.attachments.attachment_created.connect(_log_attachment_created)
    signals.attachments.attachment_deleted.connect(_log_attachment_deleted)
    signals.attachments.attachment_updated.connect(_log_attachment_updated)


def _ignore_non_loggable(f):
    """
    Only call the decorated function if the attachment/folder change
    should be logged.
    """
    @wraps(f)
    def wrapper(sender, **kwargs):
        if not kwargs.get('internal'):
            f(sender, **kwargs)

    return wrapper


def _get_folder_data(folder, for_attachment=False):
    data = folder.link_event_log_data
    if for_attachment and not folder.is_default:
        data['Folder'] = folder.title
        data['Folder ID'] = folder.id
    elif not folder.is_default:
        data['ID'] = folder.id
    return data


def _get_attachment_data(attachment):
    data = _get_folder_data(attachment.folder, True)
    data['ID'] = attachment.id
    data['Type'] = str(attachment.type.title)
    data['Title'] = attachment.title
    if attachment.type == AttachmentType.link:
        data['URL'] = attachment.link_url
    else:
        data.update({'File name': attachment.file.filename,
                     'File size': do_filesizeformat(attachment.file.size),
                     'File type': attachment.file.content_type})
    return data


def _log(folder, kind, msg, user, data, meta=None):
    if folder.link_type == LinkType.category:
        folder.category.log(CategoryLogRealm.category, kind, 'Materials', msg, user, data=data, meta=meta)
    else:
        folder.event.log(EventLogRealm.management, kind, 'Materials', msg, user, data=data, meta=meta)


@_ignore_non_loggable
def _log_folder_created(folder, user, **kwargs):
    _log(folder, LogKind.positive, f'Created folder "{folder.title}"', user, _get_folder_data(folder),
         meta={'folder_id': folder.id})


@_ignore_non_loggable
def _log_folder_deleted(folder, user, **kwargs):
    _log(folder, LogKind.negative, f'Deleted folder "{folder.title}"', user, _get_folder_data(folder),
         meta={'folder_id': folder.id})


@_ignore_non_loggable
def _log_folder_updated(folder, user, **kwargs):
    _log(folder, LogKind.change, f'Updated folder "{folder.title}"', user, _get_folder_data(folder),
         meta={'folder_id': folder.id})


@_ignore_non_loggable
def _log_attachment_created(attachment, user, **kwargs):
    if g.get('importing_event'):
        return
    _log(attachment.folder, LogKind.positive, f'Added material "{attachment.title}"', user,
         _get_attachment_data(attachment), meta={'attachment_id': attachment.id})


@_ignore_non_loggable
def _log_attachment_deleted(attachment, user, **kwargs):
    _log(attachment.folder, LogKind.negative, f'Deleted material "{attachment.title}"', user,
         _get_attachment_data(attachment), meta={'attachment_id': attachment.id})


@_ignore_non_loggable
def _log_attachment_updated(attachment, user, **kwargs):
    _log(attachment.folder, LogKind.change, f'Updated material "{attachment.title}"', user,
         _get_attachment_data(attachment), meta={'attachment_id': attachment.id})
