# This file is part of Indico.
# Copyright (C) 2002 - 2017 European Organization for Nuclear Research (CERN).
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

from functools import wraps

from jinja2.filters import do_filesizeformat

from indico.core import signals
from indico.core.db.sqlalchemy.links import LinkType
from indico.modules.attachments.models.attachments import AttachmentType
from indico.modules.events.logs import EventLogKind, EventLogRealm


def connect_log_signals():
    signals.attachments.folder_created.connect(_log_folder_created)
    signals.attachments.folder_deleted.connect(_log_folder_deleted)
    signals.attachments.folder_updated.connect(_log_folder_updated)
    signals.attachments.attachment_created.connect(_log_attachment_created)
    signals.attachments.attachment_deleted.connect(_log_attachment_deleted)
    signals.attachments.attachment_updated.connect(_log_attachment_updated)


def _ignore_non_loggable(f):
    """
    Only calls the decorated function the attachment/folder is not
    linked to a category.
    """
    @wraps(f)
    def wrapper(sender, **kwargs):
        folder = getattr(sender, 'folder', sender)  # sender may be a folder or attachment here
        if folder.link_type != LinkType.category and not kwargs.get('internal'):
            f(sender, **kwargs)

    return wrapper


def _get_folder_data(folder, for_attachment=False):
    data = folder.link_event_log_data
    if for_attachment and not folder.is_default:
        data['Folder'] = folder.title
    return data


def _get_attachment_data(attachment):
    data = _get_folder_data(attachment.folder, True)
    data['Type'] = unicode(attachment.type.title)
    data['Title'] = attachment.title
    if attachment.type == AttachmentType.link:
        data['URL'] = attachment.link_url
    else:
        data.update({'File name': attachment.file.filename,
                     'File size': do_filesizeformat(attachment.file.size),
                     'File type': attachment.file.content_type})
    return data


def _log(event, kind, msg, user, data):
    event.log(EventLogRealm.management, kind, 'Materials', msg, user, data=data)


@_ignore_non_loggable
def _log_folder_created(folder, user, **kwargs):
    event = folder.object.event_new
    _log(event, EventLogKind.positive, 'Created folder "{}"'.format(folder.title), user, _get_folder_data(folder))


@_ignore_non_loggable
def _log_folder_deleted(folder, user, **kwargs):
    event = folder.object.event_new
    _log(event, EventLogKind.negative, 'Deleted folder "{}"'.format(folder.title), user, _get_folder_data(folder))


@_ignore_non_loggable
def _log_folder_updated(folder, user, **kwargs):
    event = folder.object.event_new
    _log(event, EventLogKind.change, 'Updated folder "{}"'.format(folder.title), user, _get_folder_data(folder))


@_ignore_non_loggable
def _log_attachment_created(attachment, user, **kwargs):
    event = attachment.folder.object.event_new
    _log(event, EventLogKind.positive, 'Added material "{}"'.format(attachment.title), user,
         _get_attachment_data(attachment))


@_ignore_non_loggable
def _log_attachment_deleted(attachment, user, **kwargs):
    event = attachment.folder.object.event_new
    _log(event, EventLogKind.negative, 'Deleted material "{}"'.format(attachment.title), user,
         _get_attachment_data(attachment))


@_ignore_non_loggable
def _log_attachment_updated(attachment, user, **kwargs):
    event = attachment.folder.object.event_new
    _log(event, EventLogKind.change, 'Updated material "{}"'.format(attachment.title), user,
         _get_attachment_data(attachment))
