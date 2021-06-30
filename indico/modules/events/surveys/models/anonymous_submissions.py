# This file is part of Indico.
# Copyright (C) 2002 - 2021 CERN
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see the
# LICENSE file for more details.

from indico.core.db import db


class SurveyAnonymousSubmission(db.Model):
    __tablename__ = 'anonymous_submissions'
    __table_args__ = {'schema': 'event_surveys'}

    #: The ID of the survey
    survey_id = db.Column(
        db.Integer,
        db.ForeignKey('event_surveys.surveys.id'),
        primary_key=True,
        index=True
    )
    #: The ID of the user
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.users.id'),
        primary_key=True,
        index=True,
    )

    def __repr__(self):
        return f'<SurveyAnonymousSubmission({self.survey_id}, {self.user_id})>'
