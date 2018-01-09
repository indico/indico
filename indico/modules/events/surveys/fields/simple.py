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

from collections import Counter, OrderedDict

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
                   'absolute': OrderedDict(sorted(counter.iteritems())),
                   'relative': OrderedDict((k, v / total_answers) for k, v in sorted(counter.iteritems()))}
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
                'absolute': OrderedDict(((_('Yes'), counter[True]), (_('No'), counter[False]))),
                'relative': OrderedDict(((_('Yes'), counter[True] / total), (_('No'), counter[False] / total)))}
