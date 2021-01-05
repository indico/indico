# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from flask import session

from indico.core import signals
from indico.core.logger import Logger
from indico.modules.attachments.logging import connect_log_signals
from indico.modules.attachments.models.attachments import Attachment
from indico.modules.attachments.models.folders import AttachmentFolder
from indico.modules.attachments.util import can_manage_attachments
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


__all__ = ('logger', 'Attachment', 'AttachmentFolder')

logger = Logger.get('attachments')
connect_log_signals()


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    from indico.modules.attachments.models.attachments import Attachment, AttachmentFile
    from indico.modules.attachments.models.principals import AttachmentPrincipal, AttachmentFolderPrincipal
    Attachment.find(user_id=source.id).update({Attachment.user_id: target.id})
    AttachmentFile.find(user_id=source.id).update({AttachmentFile.user_id: target.id})
    AttachmentPrincipal.merge_users(target, source, 'attachment')
    AttachmentFolderPrincipal.merge_users(target, source, 'folder')


@signals.menu.items.connect_via('event-management-sidemenu')
def _extend_event_management_menu(sender, event, **kwargs):
    if not can_manage_attachments(event, session.user):
        return
    return SideMenuItem('attachments', _('Materials'), url_for('attachments.management', event), 80,
                        section='organization')


@signals.event_management.management_url.connect
def _get_event_management_url(event, **kwargs):
    if can_manage_attachments(event, session.user):
        return url_for('attachments.management', event)


@signals.menu.items.connect_via('category-management-sidemenu')
def _extend_category_management_menu(sender, category, **kwargs):
    return SideMenuItem('attachments', _('Materials'), url_for('attachments.management', category), icon='upload')


@signals.event_management.get_cloners.connect
def _get_attachment_cloner(sender, **kwargs):
    from indico.modules.attachments.clone import AttachmentCloner
    return AttachmentCloner


@signals.import_tasks.connect
def _import_tasks(sender, **kwargs):
    import indico.modules.attachments.tasks  # noqa: F401
