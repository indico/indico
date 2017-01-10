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

from flask import session

from indico.core import signals
from indico.core.logger import Logger
from indico.modules.events.static.models.static import StaticSite
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem

logger = Logger.get('events.static')


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    StaticSite.find(creator_id=source.id).update({StaticSite.creator_id: target.id})


@signals.menu.items.connect_via('event-management-sidemenu')
def _extend_event_management_menu(sender, event, **kwargs):
    if not event.can_manage(session.user):
        return
    return SideMenuItem('static', _('Offline Copy'), url_for('static_site.list', event), section='advanced')
