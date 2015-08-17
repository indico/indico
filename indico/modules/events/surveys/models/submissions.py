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
from indico.core.db.sqlalchemy import UTCDateTime
from indico.util.date_time import now_utc
from indico.util.string import return_ascii


class SurveySubmission(db.Model):
    __tablename__ = 'survey_submissions'
    __table_args__ = {'schema': 'events'}

    #: The ID of the submission
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the survey
    survey_id = db.Column(
        db.Integer,
        db.ForeignKey('events.surveys.id'),
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
        nullable=False,
        default=now_utc,
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

    @property
    def event(self):
        from MaKaC.conference import ConferenceHolder
        return ConferenceHolder().getById(str(self.event_id), True)

    @event.setter
    def event(self, event):
        self.event_id = int(event.getId())

    @property
    def is_anonymous(self):
        return self.user is None

    @return_ascii
    def __repr__(self):
        return '<SurveySubmission({}, {}, {})>'.format(self.id, self.survey_id, self.user_id)


class SurveyAnswer(db.Model):
    __tablename__ = 'survey_answers'
    __table_args__ = {'schema': 'events'}

    #: The ID of the submission
    submission_id = db.Column(
        db.Integer,
        db.ForeignKey('events.survey_submissions.id'),
        primary_key=True
    )
    #: The ID of the question
    question_id = db.Column(
        db.Integer,
        db.ForeignKey('events.survey_questions.id'),
        primary_key=True
    )
    #: The user's answer (no, not 42!) to the question
    data = db.Column(
        JSON,
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

    @return_ascii
    def __repr__(self):
        return '<SurveyAnswer({}, {}): {}>'.format(self.submission_id, self.question_id, self.data)
