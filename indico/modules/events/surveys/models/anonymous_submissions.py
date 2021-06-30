# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.db import db


class AnonymousSurveySubmission(db.Model):
    __tablename__ = 'anonymous_submissions'
    __table_args__ = {'schema': 'event_surveys'}

    #: The ID of the survey
    survey_id = db.Column(
        db.ForeignKey('event_surveys.surveys.id', ondelete='CASCADE'),
        primary_key=True,
        index=True
    )
    #: The ID of the user
    user_id = db.Column(
        db.ForeignKey('users.users.id', ondelete='CASCADE'),
        primary_key=True,
        index=True,
    )
    #: The Survey being submitted
    survey = db.relationship(
        'Survey',
        lazy=True,
        backref=db.backref(
            'anonymous_submissions',
            lazy='dynamic',
            cascade='all, delete-orphan',
            passive_deletes=True
        )
    )
    #: The user who submitted the survey
    user = db.relationship(
        'User',
        lazy=True,
        backref=db.backref(
            'anonymous_survey_submissions',
            lazy='dynamic',
            cascade='all, delete-orphan',
            passive_deletes=True
        )
    )

    def __repr__(self):
        return f'<AnonymousSurveySubmission({self.survey_id}, {self.user_id})>'

    @classmethod
    def merge_users(cls, target, source):
        target_ids = [anonymous_submission.survey_id for anonymous_submission in target.anonymous_survey_submissions]

        for source_anonymous_submission in source.anonymous_survey_submissions.all():
            if source_anonymous_submission.survey_id not in target_ids:
                source_anonymous_submission.user = target
            else:
                db.session.delete(source_anonymous_submission)
