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

from __future__ import unicode_literals, absolute_import

from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField
from wtforms.widgets import CheckboxInput

from indico.web.forms.widgets import JinjaWidget


class IndicoQuerySelectMultipleField(QuerySelectMultipleField):
    """Like the parent, but with a callback that allows you to modify the list

    The callback can return a new list or yield items, and you can use it e.g. to sort the list.
    """

    def __init__(self, *args, **kwargs):
        self.modify_object_list = kwargs.pop('modify_object_list', None)
        self.collection_class = kwargs.pop('collection_class', list)
        super(IndicoQuerySelectMultipleField, self).__init__(*args, **kwargs)

    def _get_object_list(self):
        object_list = super(IndicoQuerySelectMultipleField, self)._get_object_list()
        if self.modify_object_list:
            object_list = list(self.modify_object_list(object_list))
        return object_list

    def _get_data(self):
        data = super(IndicoQuerySelectMultipleField, self)._get_data()
        return self.collection_class(data)

    data = property(_get_data, QuerySelectMultipleField._set_data)


class IndicoQuerySelectMultipleCheckboxField(IndicoQuerySelectMultipleField):
    option_widget = CheckboxInput()
    widget = JinjaWidget('forms/checkbox_group_widget.html', single_kwargs=True)
