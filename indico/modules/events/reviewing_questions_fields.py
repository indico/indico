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

from __future__ import unicode_literals

from wtforms.fields import BooleanField, RadioField, StringField
from wtforms.validators import DataRequired

from indico.util.i18n import _
from indico.web.fields.base import BaseField, IndicoForm
from indico.web.fields.simple import BoolField, TextField
from indico.web.forms.widgets import JinjaWidget, SwitchWidget


class BaseReviewingQuestionConfigForm(IndicoForm):
    text = StringField(_('Question'), [DataRequired()])
    is_required = BooleanField(_('Required'), widget=SwitchWidget())

    @property
    def field_data(self):
        return {'is_required': self.is_required.data}


class RatingReviewingQuestionConfigForm(BaseReviewingQuestionConfigForm):
    no_score = BooleanField(_('Exclude from score'), widget=SwitchWidget())


class RatingReviewField(RadioField):
    widget = None

    def __init__(self, *args, **kwargs):
        question = kwargs.pop('question')
        event = question.event
        self.widget = JinjaWidget('events/reviews/rating_widget.html', question=question, inline_js=True,
                                  rating_range=event.cfa.rating_range)
        super(RatingReviewField, self).__init__(*args, **kwargs)


class RatingReviewingQuestion(BaseField):
    name = 'rating'
    friendly_name = _('Rating')
    common_settings = ('text', 'no_score')
    config_form_base = RatingReviewingQuestionConfigForm
    wtf_field_class = RatingReviewField

    @property
    def wtf_field_kwargs(self):
        range_ = self.object.event.cfa.rating_range
        return {'coerce': int, 'choices': [(n, unicode(n)) for n in range(range_[0], range_[1] + 1)],
                'question': self.object}


class BoolReviewingQuestionConfigForm(BaseReviewingQuestionConfigForm):
    pass


class BoolReviewingQuestion(BoolField, BaseField):
    common_settings = ('text',)
    config_form_base = BoolReviewingQuestionConfigForm


class TextReviewingQuestionConfigForm(BaseReviewingQuestionConfigForm):
    _order = ('text', 'is_required', 'max_length', 'max_words', 'multiline')

    @property
    def field_data(self):
        base = super(TextReviewingQuestionConfigForm, self).field_data
        return dict(base, multiline=self.multiline.data, max_words=self.max_words.data,
                    max_length=self.max_length.data)


class TextReviewingQuestion(TextField, BaseField):
    common_settings = ('text',)
    config_form_base = TextReviewingQuestionConfigForm


def get_reviewing_field_types():
    return {field.name: field for field in [RatingReviewingQuestion, BoolReviewingQuestion, TextReviewingQuestion]}
