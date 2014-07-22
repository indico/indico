# -*- coding: utf-8 -*-
##
##
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
from wtforms.fields.simple import HiddenField, TextAreaField
from wtforms.widgets.core import CheckboxInput

from indico.modules.rb.forms.widgets import PrincipalWidget
from indico.util.fossilize import fossilize
from indico.util.misc import retrieve_principals
from indico.util.string import is_valid_mail
from indico.util.i18n import _


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


class PrincipalField(HiddenField):
    widget = PrincipalWidget()

    def _convert_principal(self, principal):
        if principal['_type'] == 'Avatar':
            return u'Avatar', principal['id']
        else:
            return u'Group', principal['id']

    def process_formdata(self, valuelist):
        if valuelist:
            data = json.loads(valuelist[0])
            self.data = map(self._convert_principal, data)

    def _value(self):
        return map(fossilize, retrieve_principals(self.data))
