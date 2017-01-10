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

import json

from wtforms.fields.simple import HiddenField

from indico.util.i18n import _
from indico.web.forms.widgets import JinjaWidget


class CategoryField(HiddenField):
    """WTForms field that lets you select a category.

    :param allow_events: Whether to allow selecting a category that
                         contains events.
    :param allow_subcats: Whether to allow selecting a category that
                          contains subcategories.
    :param require_event_creation_rights: Whether to allow selecting
                                          only categories where the
                                          user can create events.
    """

    widget = JinjaWidget('forms/category_picker_widget.html')

    def __init__(self, *args, **kwargs):
        self.navigator_category_id = 0
        self.allow_events = kwargs.pop('allow_events', True)
        self.allow_subcats = kwargs.pop('allow_subcats', True)
        self.require_event_creation_rights = kwargs.pop('require_event_creation_rights', False)
        super(CategoryField, self).__init__(*args, **kwargs)

    def pre_validate(self, form):
        if self.data:
            self._validate(self.data)

    def process_data(self, value):
        if not value:
            self.data = None
            return
        try:
            self._validate(value)
        except ValueError:
            self.data = None
            self.navigator_category_id = value.id
        else:
            self.data = value
            self.navigator_category_id = value.id

    def process_formdata(self, valuelist):
        from indico.modules.categories import Category
        if valuelist:
            try:
                category_id = int(json.loads(valuelist[0])['id'])
            except KeyError:
                self.data = None
            else:
                self.data = Category.get(category_id, is_deleted=False)

    def _validate(self, category):
        if not self.allow_events and category.has_only_events:
            raise ValueError(_("Categories containing only events are not allowed."))
        if not self.allow_subcats and category.children:
            raise ValueError(_("Categories containing subcategories are not allowed."))

    def _value(self):
        return {'id': self.data.id, 'title': self.data.title} if self.data else {}

    def _get_data(self):
        return self.data
