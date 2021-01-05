# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

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
        """Generate the options' IDs."""
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
