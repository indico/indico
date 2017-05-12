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
from indico.core.roles import check_roles, ManagementRole
from indico.core.settings import SettingsProxy
from indico.modules.categories.models.categories import Category
from indico.modules.categories.models.legacy_mapping import LegacyCategoryMapping
from indico.util.i18n import _
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


logger = Logger.get('categories')

upcoming_events_settings = SettingsProxy('upcoming_events', {
    'entries': [],
    'max_entries': 10
})


@signals.import_tasks.connect
def _import_tasks(sender, **kwargs):
    import indico.modules.categories.tasks


@signals.users.merged.connect
def _merge_users(target, source, **kwargs):
    from indico.modules.categories.models.principals import CategoryPrincipal
    CategoryPrincipal.merge_users(target, source, 'category')


@signals.menu.items.connect_via('category-management-sidemenu')
def _sidemenu_items(sender, category, **kwargs):
    yield SideMenuItem('content', _('Content'), url_for('categories.manage_content', category),
                       100, icon='eye')
    yield SideMenuItem('settings', _('Settings'), url_for('categories.manage_settings', category),
                       90, icon='settings')
    yield SideMenuItem('protection', _('Protection'), url_for('categories.manage_protection', category),
                       70, icon='shield')


@signals.menu.items.connect_via('admin-sidemenu')
def _sidemenu_items(sender, **kwargs):
    if session.user.is_admin:
        yield SideMenuItem('upcoming_events', _('Upcoming events'), url_for('categories.manage_upcoming'),
                           section='homepage')


@signals.app_created.connect
def _check_roles(app, **kwargs):
    check_roles(Category)


@signals.acl.get_management_roles.connect_via(Category)
def _get_management_roles(sender, **kwargs):
    return CreatorRole


class CreatorRole(ManagementRole):
    name = 'create'
    friendly_name = _('Event creation')
    description = _('Allows creating events in the category')
