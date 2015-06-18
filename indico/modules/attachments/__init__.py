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
from indico.core.logger import Logger
from indico.util.i18n import _
from indico.web.flask.util import url_for


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
    return 'attachments', SideMenuItem(_('Attachments'), url_for('attachments.index', event),
                                       visible=event.canModify(session.user))
