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

from indico.core.db import db
from indico.core.errors import IndicoError
from indico.core.db.sqlalchemy import UTCDateTime
from indico.util.date_time import now_utc
from indico.util.string import return_ascii
from indico.util.struct.enum import IndicoEnum


class SurveyState(IndicoEnum):
    not_ready = 1
    ready_to_open = 2
    active_and_clean = 3
    active_and_answered = 4
    finished = 5


class Survey(db.Model):
    __tablename__ = 'surveys'
    __table_args__ = {'schema': 'events'}

    #: The ID of the submission
    id = db.Column(
        db.Integer,
        primary_key=True
    )
    #: The ID of the event
    event_id = db.Column(
        db.Integer,
        index=True,
        nullable=False
    )
    #: The title of the survey
    title = db.Column(
        db.String,
        nullable=False
    )
    #: The description of the survey
    description = db.Column(
        db.Text,
        nullable=False,
        default=''
    )
    #: Whether submissions will not be linked to a user
    anonymous = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )
    #: Whether submissions must be done by logged users
    require_user = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )
    #: Datetime when the survey is open
    start_dt = db.Column(
        UTCDateTime,
        nullable=True
    )
    #: Datetime when the survey is closed
    end_dt = db.Column(
        UTCDateTime,
        nullable=True
    )
    #: Whether the survey has been marked as deleted
    is_deleted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    #: The list of submissions
    submissions = db.relationship(
        'SurveySubmission',
        cascade='all, delete-orphan',
        lazy=True,
        backref=db.backref(
            'survey',
            lazy=True
        )
    )

    #: The list of questions
    questions = db.relationship(
        'SurveyQuestion',
        cascade='all, delete-orphan',
        lazy=True,
        order_by='SurveyQuestion.position',
        backref=db.backref(
            'survey',
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
    def has_ended(self):
        return bool(self.end_dt) and self.end_dt <= now_utc()

    @property
    def has_started(self):
        return bool(self.start_dt) and self.start_dt <= now_utc()

    @property
    def locator(self):
        return {'confId': self.event.id,
                'survey_id': self.id}

    @property
    def state(self):
        if not self.questions:
            return SurveyState.not_ready
        if not self.has_started:
            return SurveyState.ready_to_open
        if not self.has_ended:
            if not self.submissions:
                return SurveyState.active_and_clean
            return SurveyState.active_and_answered
        return SurveyState.finished

    @return_ascii
    def __repr__(self):
        return '<Survey({}, {})>'.format(self.id, self.event_id)

    def start(self):
        if self.state != SurveyState.ready_to_open:
            raise IndicoError("Survey can't start")
        self.start_dt = now_utc()

    def end(self):
        if self.state not in (SurveyState.active_and_clean, SurveyState.active_and_answered):
            raise IndicoError("Survey can't end")
        self.end_dt = now_utc()
