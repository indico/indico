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

from indico.core import signals
from indico.core.db.sqlalchemy.links import LinkType
from indico.core.logger import Logger
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.modules.events.logs.models.entries import EventLogKind, EventLogRealm
from indico.modules.attachments.models.attachments import AttachmentType


logger = Logger.get('attachments')


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    from indico.modules.attachments.models.attachments import Attachment, AttachmentFile
    from indico.modules.attachments.models.principals import AttachmentPrincipal, AttachmentFolderPrincipal
    Attachment.find(user_id=source.id).update({Attachment.user_id: target.id})
    AttachmentFile.find(user_id=source.id).update({AttachmentFile.user_id: target.id})
    AttachmentPrincipal.merge_users(target, source, 'attachment')
    AttachmentFolderPrincipal.merge_users(target, source, 'folder')


@signals.event_management.sidemenu.connect
def _extend_event_management_menu(event, **kwargs):
    from MaKaC.webinterface.wcomponents import SideMenuItem
    return 'attachments', SideMenuItem(_('Materials'), url_for('attachments.management', event),
                                       visible=event.canModify(session.user))


@signals.category.management_sidemenu.connect
def _extend_category_management_menu(category, **kwargs):
    from MaKaC.webinterface.wcomponents import SideMenuItem
    return 'attachments', SideMenuItem(_('Attachments'), url_for('attachments.management', category))


@signals.attachments.folder_created.connect
def _log_folder_created(folder, user, **kwargs):
    if folder.link_type == LinkType.category:
        return
    event = folder.linked_object.getConference()
    data = {'description': folder.description, 'protected': folder.is_protected}
    event.log(EventLogRealm.management, EventLogKind.positive, 'Materials', 'Created folder {}'.format(folder.title),
              user, data=data)


@signals.attachments.folder_deleted.connect
def _log_folder_deleted(folder, user, **kwargs):
    if folder.link_type == LinkType.category:
        return
    event = folder.linked_object.getConference()
    data = {'description': folder.description, 'protected': folder.is_protected}
    event.log(EventLogRealm.management, EventLogKind.change, 'Materials', 'Deleted folder {}'.format(folder.title),
              user, data=data)


def _prepare_attachment_data(attachment):
    if attachment.type == AttachmentType.link:
        data = {'url': attachment.link_url, 'title': attachment.title, 'folder': attachment.folder.title}
    else:
        file = attachment.file
        data = {'filename': file.filename, 'size': '{} kB'.format(file.size), 'folder': attachment.folder.title}

    return data


@signals.attachments.attachment_created.connect
def _log_attachment_created(attachment, user, **kwargs):
    if attachment.folder.link_type == LinkType.category:
        return
    event = attachment.folder.linked_object.getConference()
    data = _prepare_attachment_data(attachment)
    event.log(EventLogRealm.management, EventLogKind.positive, 'Materials', 'Added attachment {}'.format(attachment.title),
              user, data=data)


@signals.attachments.attachment_deleted.connect
def _log_attachment_deleted(attachment, user, **kwargs):
    if attachment.folder.link_type == LinkType.category:
        return
    event = attachment.folder.linked_object.getConference()
    data = _prepare_attachment_data(attachment)
    event.log(EventLogRealm.management, EventLogKind.change, 'Materials', 'Deleted attachment {}'.format(attachment.title),
              user, data=data)


@signals.attachments.attachment_updated.connect
def _log_attachment_updated(attachment, user, **kwargs):
    if attachment.folder.link_type == LinkType.category:
        return
    event = attachment.folder.linked_object.getConference()
    data = _prepare_attachment_data(attachment)
    event.log(EventLogRealm.management, EventLogKind.change, 'Materials', 'Updated attachment {}'.format(attachment.title),
              user, data=data)
