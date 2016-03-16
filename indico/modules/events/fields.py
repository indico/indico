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

from indico.modules.events.models.persons import EventPersonLink
from indico.modules.events.models.references import ReferenceType
from indico.modules.events.util import serialize_person_link
from indico.util.i18n import _
from indico.web.forms.fields import MultipleItemsField, PersonLinkListFieldBase
from indico.web.forms.widgets import JinjaWidget


class ReferencesField(MultipleItemsField):
    """A field to manage external references."""

    def __init__(self, *args, **kwargs):
        self.reference_class = kwargs.pop('reference_class')
        self.fields = [{'id': 'type', 'caption': _("Type"), 'type': 'select', 'required': True},
                       {'id': 'value', 'caption': _("Value"), 'type': 'text', 'required': True}]
        self.choices = {'type': {unicode(r.id): r.name for r in ReferenceType.find_all()}}
        super(ReferencesField, self).__init__(*args, uuid_field='id', uuid_field_opaque=True, **kwargs)

    def process_formdata(self, valuelist):
        super(ReferencesField, self).process_formdata(valuelist)
        if valuelist:
            existing = {x.id: x for x in self.object_data or ()}
            data = []
            for entry in self.data:
                ref = existing[int(entry['id'])] if entry.get('id') is not None else None
                type_id = int(entry['type'])
                value = entry['value']
                if ref is None or (ref.reference_type_id, ref.value) != (type_id, value):
                    # Create a new ref if it's a new entry or something changed.
                    # We never UPDATE entries as modifying persistent objects
                    # here would result in them being committed even in case
                    # form validation fails somewhere else...
                    ref = self.reference_class()
                ref.reference_type_id = type_id
                ref.value = value
                data.append(ref)
            self.data = data

    def pre_validate(self, form):
        super(ReferencesField, self).pre_validate(form)
        for reference in self.serialized_data:
            if reference['type'] not in self.choices['type']:
                raise ValueError(u'Invalid type choice: {}'.format(reference['type']))

    def _value(self):
        if not self.data:
            return []
        else:
            return [{'id': r.id, 'type': unicode(r.reference_type_id), 'value': r.value} for r in self.data]


class EventPersonLinkListField(PersonLinkListFieldBase):
    """A field to manage event's chairpersons"""

    person_link_cls = EventPersonLink
    widget = JinjaWidget('events/forms/event_person_link_widget.html')

    def __init__(self, *args, **kwargs):
        self.allow_submitters = True
        self.default_is_submitter = kwargs.pop('default_is_submitter', True)
        super(EventPersonLinkListField, self).__init__(*args, **kwargs)

    def _convert_data(self, data):
        return {self._get_person_link(x): x.pop('isSubmitter', self.default_is_submitter) for x in data}

    def _serialize_person_link(self, principal, extra_data=None):
        extra_data = extra_data or {}
        data = dict(extra_data, **serialize_person_link(principal))
        data['isSubmitter'] = principal.is_submitter
        return data

    def pre_validate(self, form):
        super(PersonLinkListFieldBase, self).pre_validate(form)
        persons = set()
        for person_link in self.data:
            if person_link.person in persons:
                raise ValueError(_("Person with email '{}' is duplicated").format(person_link.person.email))
            persons.add(person_link.person)
