# This file is part of Indico.
# Copyright (C) 2002 - 2024 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.db import db


class AnonymousSurveySubmission(db.Model):
    __tablename__ = 'anonymous_submissions'
    __table_args__ = {'schema': 'event_surveys'}

    survey_id = db.Column(
        db.ForeignKey('event_surveys.surveys.id', ondelete='CASCADE'),
        primary_key=True,
        index=True
    )
    user_id = db.Column(
        db.ForeignKey('users.users.id', ondelete='CASCADE'),
        primary_key=True,
        index=True,
    )

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
        target_ids = [sub.survey_id for sub in target.anonymous_survey_submissions]

        for sub in source.anonymous_survey_submissions.all():
            if sub.survey_id not in target_ids:
                sub.user = target
            else:
                db.session.delete(sub)
