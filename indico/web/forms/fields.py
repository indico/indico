## This file is part of Indico.
## Copyright (C) 2002 - 2014 European Organization for Nuclear Research (CERN).
##
## Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 3 of the
## License, or (at your option) any later version.
##
## Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Indico; if not, see <http://www.gnu.org/licenses/>.

import json

from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField
from wtforms.fields.simple import HiddenField, TextAreaField, PasswordField
from wtforms.widgets.core import CheckboxInput, PasswordInput

from indico.util.fossilize import fossilize
from indico.util.user import retrieve_principals
from indico.util.string import is_valid_mail
from indico.util.i18n import _
from indico.web.forms.widgets import PrincipalWidget, MultipleItemsWidget


class IndicoQuerySelectMultipleField(QuerySelectMultipleField):
    """Like the parent, but with a callback that allows you to modify the list

    The callback can return a new list or yield items, and you can use it e.g. to sort the list.
    """
    def __init__(self, *args, **kwargs):
        self.modify_object_list = kwargs.pop('modify_object_list', None)
        super(IndicoQuerySelectMultipleField, self).__init__(*args, **kwargs)

    def _get_object_list(self):
        object_list = super(IndicoQuerySelectMultipleField, self)._get_object_list()
        if self.modify_object_list:
            object_list = list(self.modify_object_list(object_list))
        return object_list


class IndicoQuerySelectMultipleCheckboxField(IndicoQuerySelectMultipleField):
    option_widget = CheckboxInput()


class JSONField(HiddenField):
    def process_formdata(self, valuelist):
        if valuelist:
            self.data = json.loads(valuelist[0])

    def _value(self):
        return json.dumps(self.data)

    def populate_obj(self, obj, name):
        # We don't want to populate an object with this
        pass


class TextListField(TextAreaField):
    def process_formdata(self, valuelist):
        if valuelist:
            self.data = [line.strip() for line in valuelist[0].split('\n') if line.strip()]
        else:
            self.data = []

    def _validate_item(self, lie):
        pass

    def pre_validate(self, form):
        for line in self.data:
            self._validate_item(line)

    def _value(self):
        return u'\n'.join(self.data) if self.data else u''


class EmailListField(TextListField):
    def _validate_item(self, line):
        if not is_valid_mail(line, False):
            raise ValueError(_(u'Invalid email address: {}').format(line))


class UnsafePasswordField(PasswordField):
    """Password field which does not hide the current value."""
    widget = PasswordInput(hide_value=False)


class PrincipalField(HiddenField):
    widget = PrincipalWidget()

    def __init__(self, *args, **kwargs):
        self.groups = kwargs.pop('groups', False)
        super(PrincipalField, self).__init__(*args, **kwargs)

    def _convert_principal(self, principal):
        if principal['_type'] == 'Avatar':
            return u'Avatar', principal['id']
        else:
            return u'Group', principal['id']

    def process_formdata(self, valuelist):
        if valuelist:
            data = json.loads(valuelist[0])
            self.data = map(self._convert_principal, data)

    def pre_validate(self, form):
        for principal in self.data:
            if not self.groups and principal[0] == 'Group':
                raise ValueError(u'You cannot select groups')

    def _value(self):
        return map(fossilize, retrieve_principals(self.data or []))


class MultipleItemsField(HiddenField):
    """A field with multiple items consisting of multiple string values.

    :param fields: A list of ``(fieldname, title)`` tuples
    """
    widget = MultipleItemsWidget()

    def __init__(self, *args, **kwargs):
        self.fields = kwargs.pop('fields')
        super(MultipleItemsField, self).__init__(*args, **kwargs)

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = json.loads(valuelist[0])

    def pre_validate(self, form):
        for item in self.data:
            if not isinstance(item, dict):
                raise ValueError(u'Invalid item type: {}'.format(type(item).__name__))
            elif item.viewkeys() != {x[0] for x in self.fields}:
                raise ValueError(u'Invalid item (bad keys): {}'.format(', '.join(item.viewkeys())))

    def _value(self):
        return self.data or []
