# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
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

from flask import redirect, request
from werkzeug.exceptions import BadRequest, NotFound

from indico.core import signals
from indico.core.logger import Logger
from indico.core.roles import check_roles, ManagementRole
from indico.modules.categories.models.categories import Category
from indico.modules.categories.models.legacy_mapping import LegacyCategoryMapping
from indico.util.i18n import _
from indico.util.string import is_legacy_id
from indico.web.flask.util import url_for
from indico.web.menu import SideMenuItem


logger = Logger.get('categories')


@signals.import_tasks.connect
def _import_tasks(sender, **kwargs):
    import indico.modules.categories.tasks


@signals.category.deleted.connect
def _category_deleted(category, **kwargs):
    if hasattr(category, '_old_id'):
        LegacyCategoryMapping.find(legacy_category_id=category._old_id).delete()


@signals.app_created.connect
def _app_created(app, **kwargs):
    """
    Handles the redirect from "broken" legacy category ids such as
    1l234 which cannot be converted to an integer without an error.
    """

    @app.before_request
    def _redirect_legacy_id():
        if not request.view_args:
            return

        categ_id = request.view_args.get('categId')
        if categ_id is None or not is_legacy_id(categ_id):
            return
        if request.method != 'GET':
            raise BadRequest('Unexpected non-GET request with legacy category ID')

        mapping = LegacyCategoryMapping.find_first(legacy_category_id=categ_id)
        if mapping is None:
            raise NotFound('Legacy category {} does not exist'.format(categ_id))

        request.view_args['categId'] = unicode(mapping.category_id)
        return redirect(url_for(request.endpoint, **dict(request.args.to_dict(), **request.view_args)), 301)


@signals.menu.items.connect_via('category-management-sidemenu-old')
def _sidemenu_items_old(sender, category, **kwargs):
    yield SideMenuItem('view', _('View category'), url_for('category.categoryDisplay', category),
                       100, icon='eye')
    yield SideMenuItem('general', _('General Settings'), url_for('category_mgmt.categoryModification', category),
                       90, icon='settings')
    yield SideMenuItem('protection', _('Protection'), url_for('category_mgmt.categoryAC', category),
                       70, icon='shield')
    yield SideMenuItem('tools', _('Tools'), url_for('category_mgmt.categoryTools', category),
                       60, icon='wrench')


@signals.menu.items.connect_via('category-management-sidemenu')
def _sidemenu_items(sender, category, **kwargs):
    yield SideMenuItem('content', _('Content'), url_for('categories.manage_content', category),
                       100, icon='eye')
    yield SideMenuItem('settings', _('Settings'), url_for('categories.manage_settings', category),
                       90, icon='settings')
    yield SideMenuItem('protection', _('Protection'), url_for('categories.manage_protection', category),
                       70, icon='shield')


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
