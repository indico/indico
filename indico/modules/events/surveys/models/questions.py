# This file is part of Indico.
# Copyright (C) 2002 - 2015 European Organization for Nuclear Research (CERN).
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

from sqlalchemy.dialects.postgresql import JSON

from indico.core.db import db
from indico.modules.events.surveys.fields import get_field_types
from indico.util.string import return_ascii


def _get_next_position(context):
    """Get the next question position for the event."""
    survey_id = context.current_parameters['survey_id']
    res = db.session.query(db.func.max(SurveyQuestion.position)).filter_by(survey_id=survey_id).one()
    return (res[0] or 0) + 1


class SurveyQuestion(db.Model):
    __tablename__ = 'survey_questions'
    __table_args__ = {'schema': 'events'}

    #: The ID of the question
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the survey
    survey_id = db.Column(
        db.Integer,
        db.ForeignKey('events.surveys.id'),
        index=True,
        nullable=False,
    )
    #: The position of the question in the survey form
    position = db.Column(
        db.Integer,
        nullable=False,
        default=_get_next_position
    )
    #: The title of the question (used as the field's label)
    title = db.Column(
        db.String,
        nullable=False
    )
    #: The description of the question (used as the field's description)
    description = db.Column(
        db.Text,
        nullable=False,
        default=''
    )
    #: If the question must be answered (wtforms DataRequired)
    is_required = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: The type of the field used for the question
    field_type = db.Column(
        db.String,
        nullable=False
    )
    #: Field-specific data (such as choices for multi-select fields)
    field_data = db.Column(
        JSON,
        nullable=False,
        default={}
    )

    # relationship backrefs:
    # - answers (SurveyAnswer.question)
    # - survey (Survey.questions)

    @property
    def field(self):
        try:
            impl = get_field_types()[self.field_type]
        except KeyError:
            return None
        return impl(self)

    @property
    def locator(self):
        return dict(self.survey.locator, question_id=self.id)

    @return_ascii
    def __repr__(self):
        return '<SurveyQuestion({}, {}, {}, {})>'.format(self.id, self.survey_id, self.field_type, self.title)

    def get_summary(self, **kwargs):
        """Returns the summary of answers submitted for this question."""
        if self.field:
            return self.field.get_summary(**kwargs)
