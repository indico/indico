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
from indico.core.db.sqlalchemy import UTCDateTime
from indico.util.date_time import now_utc
from indico.util.string import return_ascii


class Evaluation(db.Model):
    __tablename__ = 'evaluations'
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
    #: The title of the evaluation
    title = db.Column(
        db.String,
        nullable=False
    )
    #: The description of the evaluation
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
    #: Datetime when the evaluation is open
    start_dt = db.Column(
        UTCDateTime,
        nullable=False,
        default=now_utc,
    )
    #: Datetime when the evaluation is closed
    end_dt = db.Column(
        UTCDateTime,
        nullable=False,
        default=now_utc,
    )
    #: Whether the evaluation has been marked as deleted
    is_deleted = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    #: The list of submissions
    submissions = db.relationship(
        'EvaluationSubmission',
        cascade='all, delete-orphan',
        lazy=True,
        backref=db.backref(
            'evaluation',
            lazy=True
        )
    )

    #: The list of questions
    questions = db.relationship(
        'EvaluationQuestion',
        cascade='all, delete-orphan',
        lazy=True,
        backref=db.backref(
            'evaluation',
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
    def locator(self):
        return {'confId': self.event.id,
                'evaluation_id': self.id}

    @return_ascii
    def __repr__(self):
        return '<Evaluation({}, {})>'.format(self.id, self.event_id)
