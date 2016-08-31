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

from indico.modules.events.abstracts.notifications import StateCondition, TrackCondition, ContributionTypeCondition
from indico.util.decorators import classproperty
from indico.web.forms.fields import JSONField
from indico.web.forms.widgets import JinjaWidget


class EmailRuleListField(JSONField):
    """A field that stores a list of e-mail template rules."""

    CAN_POPULATE = True
    widget = JinjaWidget('events/abstracts/forms/rule_list_widget.html')
    accepted_condition_types = (StateCondition, TrackCondition, ContributionTypeCondition)

    @classproperty
    @classmethod
    def condition_class_map(cls):
        return {r.name: r for r in cls.accepted_condition_types}

    @property
    def condition_choices(self):
        return {
            c.name: {
                'title': c.description,
                'labelText': c.label_text,
                'options': list(c.get_available_values(event=self.event).viewitems()),
                'compatibleWith': c.compatible_with,
                'required': c.required
            } for c in self.accepted_condition_types
        }

    def _convert_condition(self, condition_data):
        condition_type = condition_data.pop('type')
        return self.condition_class_map[condition_type](**condition_data)

    def _convert_condition_list(self, condition_list):
        return map(self._convert_condition, condition_list)

    def _value(self):
        return super(EmailRuleListField, self)._value() if self.data else '[]'
