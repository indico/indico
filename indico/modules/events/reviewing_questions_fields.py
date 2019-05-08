# This file is part of Indico.
# Copyright (C) 2002 - 2019 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from __future__ import unicode_literals

from wtforms.fields import BooleanField
from wtforms.validators import InputRequired

from indico.modules.events.fields import RatingReviewField
from indico.util.i18n import _
from indico.web.fields.base import BaseField, FieldConfigForm
from indico.web.fields.simple import BoolField, TextField
from indico.web.forms.widgets import SwitchWidget


class AbstractRatingReviewingQuestionConfigForm(FieldConfigForm):
    no_score = BooleanField(_('Exclude from score'), widget=SwitchWidget())


class PaperRatingReviewingQuestionConfigForm(FieldConfigForm):
    pass


class AbstractRatingReviewingQuestion(BaseField):
    name = 'rating'
    friendly_name = _('Rating')
    common_settings = BaseField.common_settings + ('no_score',)
    config_form_base = AbstractRatingReviewingQuestionConfigForm
    wtf_field_class = RatingReviewField
    required_validator = InputRequired

    @property
    def wtf_field_kwargs(self):
        range_ = self.object.event.cfa.rating_range
        choices = [(n, unicode(n)) for n in range(range_[0], range_[1] + 1)]
        return {'coerce': int, 'choices': choices, 'rating_range': range_, 'question': self.object}


class PaperRatingReviewingQuestion(BaseField):
    name = 'rating'
    friendly_name = _('Rating')
    config_form_base = PaperRatingReviewingQuestionConfigForm
    wtf_field_class = RatingReviewField
    required_validator = InputRequired

    @property
    def wtf_field_kwargs(self):
        range_ = self.object.event.cfp.rating_range
        choices = [(n, unicode(n)) for n in range(range_[0], range_[1] + 1)]
        return {'coerce': int, 'choices': choices, 'rating_range': range_, 'question': self.object}


class BoolReviewingQuestion(BoolField, BaseField):
    pass


class TextReviewingQuestionConfigForm(FieldConfigForm):
    _order = ('title', 'is_required', 'description', 'max_length', 'max_words', 'multiline')


class TextReviewingQuestion(TextField, BaseField):
    config_form_base = TextReviewingQuestionConfigForm


def get_reviewing_field_types(type_):
    if type_ == 'abstracts':
        return {f.name: f for f in [AbstractRatingReviewingQuestion, BoolReviewingQuestion, TextReviewingQuestion]}
    elif type_ == 'papers':
        return {f.name: f for f in [PaperRatingReviewingQuestion, BoolReviewingQuestion, TextReviewingQuestion]}
