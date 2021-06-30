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
