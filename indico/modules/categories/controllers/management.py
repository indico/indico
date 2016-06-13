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

from sqlalchemy.orm import joinedload
from flask import redirect, flash

from indico.web.forms.base import FormDefaults
from indico.modules.categories.controllers.base import RHManageCategoryBase
from indico.modules.categories.forms import CategoryProtectionForm
from indico.modules.categories.operations import update_category
from indico.modules.categories.views import WPCategoryManagement
from indico.modules.events.util import update_object_principals
from indico.util.i18n import _
from indico.web.flask.util import url_for


class RHManageCategoryContent(RHManageCategoryBase):
    @property
    def _category_query_options(self):
        children_strategy = joinedload('children')
        children_strategy.undefer('deep_children_count')
        children_strategy.undefer('deep_events_count')
        return children_strategy,

    def _process(self):
        return WPCategoryManagement.render_template('management/content.html', self.category, 'content',
                                                    categories=self.category.children)


class RHManageCategoryProtection(RHManageCategoryBase):
    def _process(self):
        form = CategoryProtectionForm(obj=self._get_defaults(), category=self.category)
        if form.validate_on_submit():
            update_category(self.category,
                            {'protection_mode': form.protection_mode.data,
                             'no_access_contact': form.no_access_contact.data,
                             'event_creation_restricted': form.event_creation_restricted.data,
                             'event_creation_notification_emails': form.event_creation_notification_emails.data})
            update_object_principals(self.category, form.acl.data, read_access=True)
            update_object_principals(self.category, form.managers.data, full_access=True)
            update_object_principals(self.category, form.event_creators.data, role='create')
            flash(_('Protection settings of the category have been updated'), 'success')
            return redirect(url_for('.manage_protection', self.category))
        return WPCategoryManagement.render_template('management/category_protection.html', self.category, 'protection',
                                                    form=form)

    def _get_defaults(self):
        acl = {x.principal for x in self.category.acl_entries if x.read_access}
        managers = {x.principal for x in self.category.acl_entries if x.full_access}
        event_creators = {x.principal for x in self.category.acl_entries
                          if x.has_management_role('create', explicit=True)}
        return FormDefaults(self.category, acl=acl, managers=managers, event_creators=event_creators)
