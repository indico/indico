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

from flask import session, has_request_context, request

from indico.core import signals
from indico.core.logger import Logger
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.modules.attachments.legacy import connect_legacy_signals
from indico.modules.attachments.logging import connect_log_signals
from indico.modules.attachments.models.attachments import Attachment
from indico.modules.attachments.models.folders import AttachmentFolder


logger = Logger.get('attachments')
connect_log_signals()

connect_legacy_signals()


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
                                       visible=event.canModify(session.user), section='organization')


@signals.category.management_sidemenu.connect
def _extend_category_management_menu(category, **kwargs):
    from MaKaC.webinterface.wcomponents import SideMenuItem
    return 'attachments', SideMenuItem(_('Materials'), url_for('attachments.management', category))


@signals.event_management.clone.connect
def _get_attachment_cloner(event, **kwargs):
    from indico.modules.attachments.clone import AttachmentCloner
    return AttachmentCloner(event)


@signals.acl.can_access.connect_via(Attachment)
@signals.acl.can_access.connect_via(AttachmentFolder)
def _can_access(cls, obj, user, **kwargs):
    """Grant full access to attachments/folders to certain IPs"""
    from MaKaC.common import HelperMaKaCInfo
    if not has_request_context():
        return
    full_access_ips = HelperMaKaCInfo.getMaKaCInfoInstance().getIPBasedACLMgr().get_full_access_acl()
    if request.remote_addr in full_access_ips:
        return True
