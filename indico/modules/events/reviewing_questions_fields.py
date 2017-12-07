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

from wtforms.fields import BooleanField, StringField
from wtforms.validators import DataRequired

from indico.modules.events.fields import RatingReviewField
from indico.util.i18n import _
from indico.web.fields.base import BaseField, IndicoForm
from indico.web.fields.simple import BoolField, TextField
from indico.web.forms.widgets import SwitchWidget


class BaseReviewingQuestionConfigForm(IndicoForm):
    text = StringField(_('Question'), [DataRequired()])
    is_required = BooleanField(_('Required'), widget=SwitchWidget())

    @property
    def field_data(self):
        return {}


class AbstractRatingReviewingQuestionConfigForm(BaseReviewingQuestionConfigForm):
    no_score = BooleanField(_('Exclude from score'), widget=SwitchWidget())


class PaperRatingReviewingQuestionConfigForm(BaseReviewingQuestionConfigForm):
    pass


class AbstractRatingReviewingQuestion(BaseField):
    name = 'rating'
    friendly_name = _('Rating')
    common_settings = ('text', 'no_score', 'is_required')
    config_form_base = AbstractRatingReviewingQuestionConfigForm
    wtf_field_class = RatingReviewField

    @property
    def wtf_field_kwargs(self):
        range_ = self.object.event.cfa.rating_range
        choices = [(n, unicode(n)) for n in range(range_[0], range_[1] + 1)]
        return {'coerce': int, 'choices': choices, 'rating_range': range_, 'question': self.object}


class PaperRatingReviewingQuestion(BaseField):
    name = 'rating'
    friendly_name = _('Rating')
    common_settings = ('text', 'no_score', 'is_required')
    config_form_base = PaperRatingReviewingQuestionConfigForm
    wtf_field_class = RatingReviewField

    @property
    def wtf_field_kwargs(self):
        range_ = self.object.event.cfp.rating_range
        choices = [(n, unicode(n)) for n in range(range_[0], range_[1] + 1)]
        return {'coerce': int, 'choices': choices, 'rating_range': range_, 'question': self.object}


class BoolReviewingQuestion(BoolField, BaseField):
    common_settings = ('text', 'is_required')
    config_form_base = BaseReviewingQuestionConfigForm


class TextReviewingQuestionConfigForm(BaseReviewingQuestionConfigForm):
    _order = ('text', 'is_required', 'max_length', 'max_words', 'multiline')

    @property
    def field_data(self):
        base = super(TextReviewingQuestionConfigForm, self).field_data
        return dict(base, multiline=self.multiline.data, max_words=self.max_words.data,
                    max_length=self.max_length.data)


class TextReviewingQuestion(TextField, BaseField):
    common_settings = ('text', 'is_required')
    config_form_base = TextReviewingQuestionConfigForm


def get_reviewing_field_types(type_):
    if type_ == 'abstracts':
        return {f.name: f for f in [AbstractRatingReviewingQuestion, BoolReviewingQuestion, TextReviewingQuestion]}
    elif type_ == 'papers':
        return {f.name: f for f in [PaperRatingReviewingQuestion, BoolReviewingQuestion, TextReviewingQuestion]}
