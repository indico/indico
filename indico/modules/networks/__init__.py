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

from flask import has_request_context, request, session

from indico.core import signals
from indico.core.logger import Logger
from indico.modules.attachments import Attachment, AttachmentFolder
from indico.modules.networks.models.networks import IPNetworkGroup
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


logger = Logger.get('networks')


@signals.menu.items.connect_via('admin-sidemenu')
def _sidemenu_items(sender, **kwargs):
    if session.user.is_admin:
        yield SideMenuItem('ip_networks', _('IP Networks'), url_for('networks.manage'), section='security')


@signals.acl.can_access.connect_via(Attachment)
@signals.acl.can_access.connect_via(AttachmentFolder)
def _can_access(cls, obj, user, authorized, **kwargs):
    # Grant full access to attachments/folders to certain networks
    if not has_request_context() or not request.remote_addr or authorized is not None:
        return
    ip = unicode(request.remote_addr)
    if any(net.contains_ip(ip) for net in IPNetworkGroup.query.filter_by(attachment_access_override=True)):
        return True
