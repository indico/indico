# This file is part of Indico.
# Copyright (C) 2002 - 2018 European Organization for Nuclear Research (CERN).
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

from __future__ import division, unicode_literals

import uuid
from collections import Counter, OrderedDict
from copy import deepcopy

from indico.modules.events.surveys.fields.base import SurveyField
from indico.util.i18n import _
from indico.util.string import alpha_enum
from indico.web.fields.choices import MultiSelectField, SingleChoiceField


class _AddUUIDMixin(object):
    @staticmethod
    def process_imported_data(data):
        """Generate the options' IDs"""
        data = deepcopy(data)
        if 'options' in data:
            for option in data['options']:
                option['id'] = unicode(uuid.uuid4())
        return data


class SurveySingleChoiceField(_AddUUIDMixin, SingleChoiceField, SurveyField):
    def get_summary(self):
        counter = Counter()
        for answer in self.object.answers:
            counter[answer.data] += 1
        total = sum(counter.values())
        options = self.object.field_data['options']
        if counter[None]:
            no_option = {'id': None, 'option': _("No selection")}
            options.append(no_option)
        return {'total': total,
                'labels': [alpha_enum(val).upper() for val in xrange(len(options))],
                'absolute': OrderedDict((opt['option'], counter[opt['id']]) for opt in options),
                'relative': OrderedDict((opt['option'], counter[opt['id']] / total) for opt in options)}


class SurveyMultiSelectField(_AddUUIDMixin, MultiSelectField, SurveyField):
    def get_summary(self):
        counter = Counter()
        for answer in self.object.answers:
            counter.update(answer.data)
        total = sum(counter.values())
        options = self.object.field_data['options']
        return {'total': total,
                'labels': [alpha_enum(val).upper() for val in xrange(len(options))],
                'absolute': OrderedDict((opt['option'], counter[opt['id']]) for opt in options),
                'relative': OrderedDict((opt['option'], counter[opt['id']] / total if total else 0) for opt in options)}
