# This file is part of Indico.
# Copyright (C) 2002 - 2023 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from marshmallow.fields import List, Nested, Raw, String

from indico.core.marshmallow import mm
from indico.modules.events.surveys.models.submissions import SurveyAnswer, SurveySubmission


class SurveyAnswerSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = SurveyAnswer
        fields = ('question_id', 'question_title', 'answer')

    answer = Raw(attribute='data')
    question_title = String(attribute='question.title')


class SurveySubmissionSchema(mm.SQLAlchemyAutoSchema):
    class Meta:
        model = SurveySubmission
        fields = ('id', 'survey_id', 'survey_title', 'submitted_dt', 'is_anonymous', 'is_submitted', 'pending_answers',
                  'answers')

    survey_title = String(attribute='survey.title')
    answers = List(Nested(SurveyAnswerSchema))
