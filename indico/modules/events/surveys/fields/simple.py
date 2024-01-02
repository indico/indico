# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from collections import Counter

from indico.modules.events.surveys.fields.base import SurveyField
from indico.util.i18n import _
from indico.web.fields.simple import BoolField, NumberField, TextField


class SurveyTextField(TextField, SurveyField):
    def get_summary(self):
        if not self.object.not_empty_answers:
            return
        return [a.data for a in self.object.not_empty_answers]


class SurveyNumberField(NumberField, SurveyField):
    def get_summary(self):
        counter = Counter()
        for answer in self.object.not_empty_answers:
            counter[answer.data] += 1
        if not counter:
            return
        total_answers = sum(counter.values())
        results = {'total': sum(counter.elements()),
                   'max': max(counter.elements()),
                   'min': min(counter.elements()),
                   'absolute': dict(sorted(counter.items())),
                   'relative': {k: v / total_answers for k, v in sorted(counter.items())}}
        results['average'] = results['total'] / len(list(counter.elements()))
        return results


class SurveyBoolField(BoolField, SurveyField):
    def get_summary(self):
        counter = Counter()
        for answer in self.object.not_empty_answers:
            counter[answer.data] += 1
        if not counter:
            return
        total = sum(counter.values())
        return {'total': total,
                'absolute': {_('Yes'): counter[True], _('No'): counter[False]},
                'relative': {_('Yes'): counter[True] / total, _('No'): counter[False] / total}}
