# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from sqlalchemy.dialects.postgresql import JSONB

from indico.core.db import db
from indico.core.db.sqlalchemy import UTCDateTime
from indico.core.db.sqlalchemy.util.queries import increment_and_get


def _get_next_friendly_id(context):
    """Get the next friendly id for a survey submission."""
    from indico.modules.events.surveys.models.surveys import Survey
    survey_id = context.current_parameters['survey_id']
    assert survey_id is not None
    return increment_and_get(Survey._last_friendly_submission_id, Survey.id == survey_id)


class SurveySubmission(db.Model):
    __tablename__ = 'submissions'
    __table_args__ = (db.CheckConstraint('is_anonymous OR user_id IS NOT NULL', 'anonymous_or_user'),
                      db.CheckConstraint('is_submitted = (submitted_dt IS NOT NULL)',
                                         'dt_set_when_submitted'),
                      db.CheckConstraint('(is_submitted AND is_anonymous) = (user_id IS NULL)',
                                         'submitted_and_anonymous_no_user'),
                      {'schema': 'event_surveys'})

    #: The ID of the submission
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The human-friendly ID of the submission
    friendly_id = db.Column(
        db.Integer,
        nullable=False,
        default=_get_next_friendly_id
    )
    #: The ID of the survey
    survey_id = db.Column(
        db.Integer,
        db.ForeignKey('event_surveys.surveys.id'),
        index=True,
        nullable=False
    )
    #: The ID of the user who submitted the survey
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        index=True,
        nullable=True
    )
    #: The date/time when the survey was submitted
    submitted_dt = db.Column(
        UTCDateTime,
        nullable=True,
    )
    #: Whether the survey submission is anonymous
    is_anonymous = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: Whether the survey was submitted
    is_submitted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: List of non-submitted answers
    pending_answers = db.Column(
        JSONB,
        default={}
    )

    #: The user who submitted the survey
    user = db.relationship(
        'User',
        lazy=True,
        backref=db.backref(
            'survey_submissions',
            lazy='dynamic'
        )
    )
    #: The list of answers
    answers = db.relationship(
        'SurveyAnswer',
        cascade='all, delete-orphan',
        lazy=True,
        backref=db.backref(
            'submission',
            lazy=True
        )
    )

    # relationship backrefs:
    # - survey (Survey.submissions)

    @property
    def locator(self):
        return dict(self.survey.locator, submission_id=self.id)

    def __repr__(self):
        return f'<SurveySubmission({self.id}, {self.survey_id}, {self.user_id})>'


class SurveyAnswer(db.Model):
    __tablename__ = 'answers'
    __table_args__ = {'schema': 'event_surveys'}

    #: The ID of the submission
    submission_id = db.Column(
        db.Integer,
        db.ForeignKey('event_surveys.submissions.id'),
        primary_key=True
    )
    #: The ID of the question
    question_id = db.Column(
        db.Integer,
        db.ForeignKey('event_surveys.items.id'),
        primary_key=True
    )
    #: The user's answer (no, not 42!) to the question
    data = db.Column(
        JSONB,
        nullable=False
    )

    #: The list of answers
    question = db.relationship(
        'SurveyQuestion',
        lazy=True,
        backref=db.backref(
            'answers',
            cascade='all, delete-orphan',
            lazy=True
        )
    )

    # relationship backrefs:
    # - submission (SurveySubmission.answers)

    @property
    def is_empty(self):
        return self.question.field.is_value_empty(self)

    def __repr__(self):
        return f'<SurveyAnswer({self.submission_id}, {self.question_id}): {self.data}>'

    @property
    def answer_data(self):
        return self.question.field.get_friendly_value(self.data)
