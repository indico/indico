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

from indico.modules.events.models.references import ReferenceType
from indico.util.i18n import _
from indico.web.forms.fields import MultipleItemsField


class ReferencesField(MultipleItemsField):
    """A field to manage external references."""
    def __init__(self, *args, **kwargs):
        self.reference_class = kwargs.pop('reference_class')
        self.fields = [{'id': 'type', 'caption': _("Type"), 'type': 'select', 'required': True},
                       {'id': 'value', 'caption': _("Value"), 'type': 'text', 'required': True}]
        self.choices = {'type': {unicode(r.id): r.name for r in ReferenceType.find_all()}}
        super(ReferencesField, self).__init__(*args, **kwargs)

    def process_formdata(self, valuelist):
        super(ReferencesField, self).process_formdata(valuelist)
        if valuelist:
            self.data = [self.reference_class(reference_type_id=int(r['type']), value=r['value']) for r in self.data]

    def pre_validate(self, form):
        super(ReferencesField, self).pre_validate(form)
        for reference in self.serialized_data:
            if reference['type'] not in self.choices['type']:
                raise ValueError(u'Invalid type choice: {}'.format(reference['type']))

    def _value(self):
        return [{'type': unicode(r.reference_type_id), 'value': r.value} for r in self.data] if self.data else []
